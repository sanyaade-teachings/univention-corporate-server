#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
## desc: Change password via User Settings
## packages:
##  - univention-management-console-module-udm
##  - univention-management-console-module-passwordchange
## roles-not:
##  - memberserver
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import time

from ldap.filter import filter_format
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions

import univention.admin.modules as udm_modules
import univention.testing.selenium.udm as selenium_udm
import univention.testing.strings as uts
import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test
from univention.admin import localization
from univention.testing import selenium
from univention.testing.ucs_samba import password_policy, wait_for_drs_replication
from univention.testing.utils import get_ldap_connection


translator = localization.translation('ucs-test-selenium')
_ = translator.translate


class PasswordChangeError(Exception):
    pass


class PasswordTooSimpleError(Exception):
    pass


class PasswordTooShortError(Exception):
    pass


class PasswordReuseError(Exception):
    pass


class User(object):
    def __init__(self, username, lastname, password='univention'):
        self.username = username
        self.lastname = lastname
        self.password = password


def random_password():
    s = uts.random_string()
    return f'{s[:5]}%{s[5:10]}'


class UMCTester(object):

    def test_umc(self):
        self.add_default_password_policy()
        old_samba_settings = self.get_samba_settings()
        self.set_samba_settings({
            'passwordHistory': '3',
            'domainPasswordComplex': '0',
        })

        try:
            self.test_password_change(self.admin, random_password())
            self.test_password_change(self.regular_user, random_password())
            self.test_usability_of_a_module_after_password_change(self.admin, random_password())
            self.check_for_short_password_error(self.admin)
            # FIXME: admins can somehow always reuse passwords in a samba domain; testing with regular user only on this point
            self.check_for_password_reuse_error(self.regular_user)
            self.check_change_password_on_login(self.admin, random_password())
        finally:
            self.set_samba_settings(old_samba_settings)

    def add_default_password_policy(self):
        self.udm.create_object(
            'policies/pwhistory',
            name='ucs-test_pw_policy',
            length='3',
            pwLength='8',
            position='cn=pwhistory,cn=users,cn=policies,%s' % (self.selenium.ldap_base,),
        )

        self.udm.modify_object(
            'container/cn',
            dn='cn=testusers,cn=users,%s' % (self.selenium.ldap_base,),
            policy_reference='cn=ucs-test_pw_policy,cn=pwhistory,cn=users,cn=policies,%s' % (self.selenium.ldap_base,),
        )

    def _get_samba_obj(self):
        ucr = ucr_test.UCSTestConfigRegistry()
        ucr.load()
        lo = get_ldap_connection()
        udm_modules.update()
        samba_module = udm_modules.get('settings/sambadomain')
        obj = samba_module.object(None, lo, None, 'sambaDomainName=%s,cn=samba,%s' % (ucr.get('windows/domain'), ucr.get('ldap/base')))
        obj.open()
        return obj

    def get_samba_settings(self):
        obj = self._get_samba_obj()
        return {
            'passwordHistory': obj['passwordHistory'],
            'domainPasswordComplex': obj['domainPasswordComplex'],
        }

    def set_samba_settings(self, settings):
        obj = self._get_samba_obj()
        for key, value in settings.items():
            obj[key] = value
        obj.modify()

    def test_password_change(self, user, new_password):
        self.selenium.do_login(user.username, user.password)
        # give some time for the possible udm/license check
        # which fails if we change the password to fast
        time.sleep(5)
        old_password = user.password
        user.password = new_password
        self.change_own_password(old_password, user.password)
        self.selenium.end_umc_session()
        self.selenium.do_login(user.username, user.password)
        self.selenium.end_umc_session()

    def test_usability_of_a_module_after_password_change(self, user, new_password):
        users = selenium_udm.Users(self.selenium)

        self.selenium.do_login(user.username, user.password)
        self.selenium.open_module(_('Users'))
        users.wait_for_main_grid_load()

        old_password = user.password
        user.password = new_password
        self.change_own_password(old_password, user.password)

        users.open_details(vars(user))
        self.selenium.end_umc_session()

    def check_for_short_password_error(self, user):
        self.selenium.do_login(user.username, user.password)
        try:
            self.change_own_password(user.password, 'a')
            raise PasswordChangeError('It was possible to assign a too short password.')
        except PasswordTooShortError:
            self.selenium.end_umc_session()

    def check_for_password_reuse_error(self, user):
        self.selenium.do_login(user.username, user.password)
        try:
            self.change_own_password(user.password, user.password)
            raise PasswordChangeError('It was possible to reuse a password.')
        except PasswordReuseError:
            self.selenium.end_umc_session()

    def check_change_password_on_login(self, user, new_password):
        self.selenium.do_login(user.username, user.password)
        self.set_change_password_on_login_flag(user)
        self.selenium.end_umc_session()

        old_password = user.password
        user.password = new_password
        self.login_while_changing_password(user.username, old_password, user.password)

    def set_change_password_on_login_flag(self, user):
        users = selenium_udm.Users(self.selenium)

        self.selenium.open_module(_('Users'))
        users.wait_for_main_grid_load()
        users.open_details(vars(user))
        # FIXME: Sleeping here, because for some reason the Account tab doesn't
        # react to clicks for a while when the detailsPage just loaded up.
        time.sleep(5)
        self.selenium.click_tab(_('Account'))
        self.selenium.wait_for_text(_('User has to change password on next login'))
        self.selenium.click_text(_('User has to change password on next login'))
        users.save_details()
        # sleep some more, must be synced to samba
        time.sleep(3)
        wait_for_drs_replication(filter_format('(&(cn=%s)(pwdLastSet=0))', (user.username,)))

    def login_while_changing_password(self, username, old_password, new_password):
        self.submit_login_credentials(username, old_password)
        self.selenium.wait_for_text(_('password has expired and must be renewed'))
        self.selenium.enter_input('new_password', new_password)
        # FIXME: Thing get dirty here, because the input field for the password
        # retype has no name.
        elem = self.selenium.driver.find_element(By.XPATH, '//input[@id="umcLoginNewPasswordRetype"]')
        elem.clear()
        elem.send_keys(new_password)
        elem.submit()
        self.check_if_login_was_successful()
        self.selenium.end_umc_session()

        for i in range(3):
            try:
                self.selenium.do_login(username, new_password)
            except Exception:
                pass
            else:
                exc = None
                break
            finally:
                self.selenium.end_umc_session()
            time.sleep(10)
        if exc:
            raise exc

    def submit_login_credentials(self, username, password):
        self.selenium.driver.get(
            self.selenium.base_url + 'univention/login/?lang=%s'
            % (self.selenium.language,),
        )
        self.selenium.wait_until(
            expected_conditions.presence_of_element_located(
                (webdriver.common.by.By.ID, "umcLoginUsername"),
            ),
        )
        self.selenium.enter_input('username', username)
        self.selenium.enter_input('password', password)
        self.selenium.submit_input('password')

    def check_if_login_was_successful(self):
        self.selenium.wait_for_any_text_in_list([
            _('Favorites'),
            _('no module available'),
        ])
        try:
            self.selenium.wait_for_text(_('no module available'), timeout=1)
            self.selenium.click_button(_('Ok'))
            self.selenium.wait_until_all_dialogues_closed()
        except TimeoutException:
            pass

    def change_own_password(self, old_password, new_password):
        self.selenium.open_side_menu()
        self.selenium.click_text(_('User settings'))
        self.selenium.click_text(_('Change password'))
        self.selenium.wait_for_text(_("Change the password of"))
        try:
            self.selenium.enter_input('password', old_password)
        except WebDriverException:
            time.sleep(5)
            self.selenium.enter_input('password', old_password)
        self.selenium.enter_input('new_password_1', new_password)
        self.selenium.enter_input('new_password_2', new_password)
        self.selenium.click_button(_('Change password'))
        self.selenium.wait_for_any_text_in_list([
            _('password has been changed'),
            _('password was already used'),
            _('password is too short'),
            _('password is too simple'),
        ])
        try:
            self.selenium.wait_for_text(_('password was already used'), timeout=1)
            raise PasswordReuseError(new_password)
        except TimeoutException:
            pass
        try:
            self.selenium.wait_for_text(_('password is too simple'), timeout=1)
            raise PasswordTooSimpleError(new_password)
        except TimeoutException:
            pass
        try:
            self.selenium.wait_for_text(_('password is too short'), timeout=1)
            raise PasswordTooShortError(new_password)
        except TimeoutException:
            pass
        self.selenium.click_button(_('Ok'))
        self.selenium.wait_until_all_dialogues_closed()


if __name__ == '__main__':
    with udm_test.UCSTestUDM() as udm, selenium.UMCSeleniumTest() as s, password_policy(maximum_password_age=3):
        umc_tester = UMCTester()
        umc_tester.udm = udm
        umc_tester.selenium = s

        test_user_cn = umc_tester.udm.create_object(
            'container/cn',
            name='testusers',
            position='cn=users,%s' % (umc_tester.udm.LDAP_BASE,),
        )

        lo = get_ldap_connection()

        regular_dn, regular_username = umc_tester.udm.create_user(
            password='univention',
            position=test_user_cn,
        )
        regular_user = lo.get(regular_dn)

        admin_dn, admin_username = umc_tester.udm.create_user(
            password='univention',
            position=test_user_cn,
            primaryGroup='cn=Domain Admins,cn=groups,%s' % (umc_tester.udm.LDAP_BASE,),
        )
        admin_user = lo.get(admin_dn)

        umc_tester.admin = User(admin_username, admin_user['sn'][0], password='univention')
        umc_tester.regular_user = User(regular_username, regular_user['sn'][0], password='univention')

        umc_tester.test_umc()
