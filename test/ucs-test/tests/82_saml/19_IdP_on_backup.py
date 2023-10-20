#!/usr/share/ucs-test/runner python3
## desc: Check whether idP is synchronized between DC Master and DC Backup.
## tags:
##  - saml
## bugs: [39479]
## roles: [domaincontroller_backup]
## join: true
## exposure: dangerous

import socket
import time

import univention.admin.modules as udm_modules
import univention.config_registry as configRegistry
from univention.testing import utils

import samltest


ucr = configRegistry.ConfigRegistry()
ucr.load()
udm_modules.update()


def main():
    account = utils.UCSTestDomainAdminCredentials()
    SamlSession = samltest.SamlTest(account.username, account.bindpw)
    lo = utils.get_ldap_connection(admin_uldap=True)
    master = udm_modules.lookup('computers/domaincontroller_master', None, lo, scope='sub')
    master_hostname = f"{master[0]['name']}.{master[0]['domain']}"
    master_ip = socket.gethostbyname(master_hostname)
    backup_ip = '127.0.0.1'

    try:
        with samltest.GuaranteedIdP(master_ip):
            SamlSession.login_with_new_session_at_IdP()
            SamlSession.test_logged_in_status()
            time.sleep(1)
        SamlSession.target_sp_hostname = master_hostname
        with samltest.GuaranteedIdP(backup_ip):
            SamlSession.login_with_existing_session_at_IdP()
            SamlSession.test_logged_in_status()
    except samltest.SamlError as exc:
        utils.fail(str(exc))


if __name__ == '__main__':
    main()
