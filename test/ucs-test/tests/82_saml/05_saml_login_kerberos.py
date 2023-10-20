#!/usr/share/ucs-test/runner python3
## desc: SSO Login at UMC as Service Provider with kerberos
## tags: [saml]
## join: true
## exposure: dangerous
## roles: [domaincontroller_master]
## packages:
##   - univention-samba4
## tags:
##  - skip_admember

import subprocess

import univention.testing.ucr as ucr_test
from univention.config_registry import handler_set
from univention.testing import utils

import samltest


class KerberosTicket:
    def __init__(self, hostname,):
        self.hostname = hostname

    def __enter__(self):
        subprocess.call(['kdestroy'])
        subprocess.check_call(['kinit', '--password-file=/etc/machine.secret', self.hostname + '$'])  # get kerberos ticket

    def __exit__(self, exc_type, exc_value, traceback,):
        subprocess.check_call(['kdestroy'])


def main():
    with ucr_test.UCSTestConfigRegistry() as ucr:
        hostname = ucr['hostname']
        handler_set(['kerberos/defaults/rdns=false', "saml/idp/authsource=univention-negotiate"])
        with KerberosTicket(hostname):
            SamlSession = samltest.SamlTest('', '', use_kerberos=True,)
            try:
                SamlSession.login_with_new_session_at_IdP()
                SamlSession.test_logged_in_status()
                SamlSession.logout_at_IdP()
                SamlSession.test_logout_at_IdP()
                SamlSession.test_logout()
            except samltest.SamlError as exc:
                utils.fail(str(exc))


if __name__ == '__main__':
    main()
    print("####Success: SSO login is working####")
