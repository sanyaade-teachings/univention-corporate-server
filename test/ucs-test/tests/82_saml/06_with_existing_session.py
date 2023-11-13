#!/usr/share/ucs-test/runner python3
## desc: Test passwordless login at SP with existing session at IdP
## tags: [saml]
## roles-not: [domaincontroller_master]
## join: true
## packages:
##   - univention-saml
## exposure: safe
## tags:
##  - skip_admember

import univention.admin.modules as udm_modules
from univention.testing import utils

import samltest


udm_modules.update()


def main():
    account = utils.UCSTestDomainAdminCredentials()
    SamlSession = samltest.SamlTest(account.username, account.bindpw)
    lo = utils.get_ldap_connection(admin_uldap=True)

    master = udm_modules.lookup('computers/domaincontroller_master', None, lo, scope='sub')
    master_hostname = "%s.%s" % (master[0]['name'], master[0]['domain'])
    try:
        SamlSession.login_with_new_session_at_IdP()
        SamlSession.test_logged_in_status()
        SamlSession.target_sp_hostname = master_hostname
        SamlSession.login_with_existing_session_at_IdP()
        SamlSession.test_logged_in_status()
    except samltest.SamlError as exc:
        utils.fail(str(exc))


if __name__ == '__main__':
    main()
    print("Success: SSO with existing session is working")
