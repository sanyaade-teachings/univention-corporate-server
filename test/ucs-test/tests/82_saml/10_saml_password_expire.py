#!/usr/share/ucs-test/runner python3
## desc: Check whether SSO is not possible with expired password flag on user account
## tags: [saml,skip_admember]
## join: true
## exposure: dangerous

import pytest

import univention.testing.udm as udm_test
from univention.testing.utils import get_ldap_connection

import samltest


def main():
    test_normal_user()
    test_kinit_user()
    test_k5key_user()


def test_normal_user():
    with udm_test.UCSTestUDM() as udm:
        username = udm.create_user(pwdChangeNextLogin='1')[1]
        # wrong password
        SamlSession = samltest.SamlTest(username, 'aaaunivention',)
        with pytest.raises(samltest.SamlAuthenticationFailed):
            SamlSession.login_with_new_session_at_IdP()
        # correct password
        SamlSession = samltest.SamlTest(username, 'univention',)
        with pytest.raises(samltest.SamlPasswordExpired):
            SamlSession.login_with_new_session_at_IdP()


def test_kinit_user():
    with udm_test.UCSTestUDM() as udm:
        dn, username = udm.create_user(pwdChangeNextLogin='1')
        lo = get_ldap_connection()
        lo.modify(dn, [('userPassword', lo.get(dn, ['userPassword'],)['userPassword'], [b'{KINIT}'])],)
        udm.verify_ldap_object(dn, {'userPassword': ['{KINIT}']},)
        # wrong password
        SamlSession = samltest.SamlTest(username, 'aaaunivention',)
        with pytest.raises(samltest.SamlAuthenticationFailed):
            SamlSession.login_with_new_session_at_IdP()
        # correct password
        SamlSession = samltest.SamlTest(username, 'univention',)
        with pytest.raises(samltest.SamlPasswordExpired):
            SamlSession.login_with_new_session_at_IdP()


def test_k5key_user():
    with udm_test.UCSTestUDM() as udm:
        dn, username = udm.create_user(pwdChangeNextLogin='1')
        lo = get_ldap_connection()
        lo.modify(dn, [('userPassword', lo.get(dn, ['userPassword'],)['userPassword'], [b'{K5KEY}'])],)
        udm.verify_ldap_object(dn, {'userPassword': ['{K5KEY}']},)
        # wrong password
        SamlSession = samltest.SamlTest(username, 'aaaunivention',)
        with pytest.raises(samltest.SamlAuthenticationFailed):
            SamlSession.login_with_new_session_at_IdP()
        # correct password
        SamlSession = samltest.SamlTest(username, 'univention',)
        with pytest.raises(samltest.SamlPasswordExpired):
            SamlSession.login_with_new_session_at_IdP()


if __name__ == '__main__':
    main()
    print("Success: Login with pwdChangeNextLogin='1' set is not possible")
