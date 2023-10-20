#!/usr/share/ucs-test/runner python3
## desc: Check whether SSO is not possible with wrong password
## tags:
##  - saml
##  - univention
## join: true
## exposure: dangerous
## tags:
##  - skip_admember

import pytest

import univention.testing.udm as udm_test

import samltest


def main():
    with udm_test.UCSTestUDM() as udm:
        testcase_user_name = udm.create_user()[1]
        SamlSession = samltest.SamlTest(testcase_user_name, 'Wrong password',)

        with pytest.raises(samltest.SamlAuthenticationFailed):
            SamlSession.login_with_new_session_at_IdP()


if __name__ == '__main__':
    main()
    print("Success: It is not possible to login with a wrong password")
