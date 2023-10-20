#!/usr/share/ucs-test/runner python3
## desc: Check whether SSO is not possible with non existing user account
## tags:
##  - saml
##  - univention
## join: true
## exposure: dangerous
## tags:
##  - skip_admember

import pytest

import samltest


def main():
    SamlSession = samltest.SamlTest('NonExistent3.14', 'univention')

    with pytest.raises(samltest.SamlAuthenticationFailed):
        SamlSession.login_with_new_session_at_IdP()


if __name__ == '__main__':
    main()
    print("Success: It is not possible to login with non existing account")
