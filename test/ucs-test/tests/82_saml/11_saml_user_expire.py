#!/usr/share/ucs-test/runner python3
## desc: Check whether SSO is not possible with expired user account
## tags:
##  - saml
##  - univention
## join: true
## exposure: dangerous
## tags:
##  - skip_admember

from datetime import datetime, timedelta

import pytest

import univention.testing.udm as udm_test

import samltest


def main():
    test_expired_account()
    test_unexpired_account()


def test_expired_account():
    yesterday = datetime.now() - timedelta(days=1)
    with udm_test.UCSTestUDM() as udm:
        testcase_user_name = udm.create_user(userexpiry=yesterday.isoformat()[:10])[1]
        SamlSession = samltest.SamlTest(testcase_user_name, 'aaaunivention')
        with pytest.raises(samltest.SamlAuthenticationFailed):
            SamlSession.login_with_new_session_at_IdP()
        SamlSession = samltest.SamlTest(testcase_user_name, 'univention')
        with pytest.raises(samltest.SamlAccountExpired):
            SamlSession.login_with_new_session_at_IdP()


def test_unexpired_account():
    tomorrow = datetime.now() + timedelta(days=1)
    with udm_test.UCSTestUDM() as udm:
        testcase_user_name = udm.create_user(userexpiry=tomorrow.isoformat()[:10])[1]
        SamlSession = samltest.SamlTest(testcase_user_name, 'univention')
        SamlSession.login_with_new_session_at_IdP()
        SamlSession.test_logged_in_status()


if __name__ == '__main__':
    main()
    print("Success: It is not possible to login with expired account")
