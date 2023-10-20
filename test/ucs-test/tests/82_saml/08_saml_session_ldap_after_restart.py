#!/usr/share/ucs-test/runner python3
## desc: Check if SSO session is still active after LDAP server restart
## tags: [saml]
## roles: [domaincontroller_master]
## exposure: dangerous
## tags:
##  - skip_admember

import subprocess

from univention.testing import utils

import samltest


def main():

    account = utils.UCSTestDomainAdminCredentials()

    SamlSession = samltest.SamlTest(account.username, account.bindpw)
    SamlSession.login_with_new_session_at_IdP()
    subprocess.call(['/etc/init.d/slapd', 'restart'])
    SamlSession.test_logged_in_status()


if __name__ == '__main__':
    main()
    print("Success: SSO session is still working after slapd restart")
