#!/usr/share/ucs-test/runner python3
## desc: Test handling of multiple certs in cert.pem
## tags: [saml]
## bugs: [47700]
## join: true
## roles: [domaincontroller_master]
## exposure: dangerous
## tags:
##  - skip_admember

import os

from univention.testing import utils

import samltest


def main():
    cert_folder = samltest.SPCertificate.get_server_cert_folder()
    with open(os.path.join(cert_folder, 'cert.pem',), 'rb',) as cert_file:
        cert = cert_file.read()
    with open('/etc/univention/ssl/ucsCA/CAcert.pem', 'rb',) as ca_file:
        cert += b'\n' + ca_file.read()
    with samltest.SPCertificate(cert):
        saml_check()


def saml_check():
    account = utils.UCSTestDomainAdminCredentials()
    SamlSession = samltest.SamlTest(account.username, account.bindpw,)
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
