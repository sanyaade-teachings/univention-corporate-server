#!/usr/share/ucs-test/runner python3
## desc: Test SSO with supplement entityID
## tags: [saml]
## join: true
## exposure: dangerous
## roles: [domaincontroller_master, domaincontroller_backup]
## tags:
##  - skip_admember

import subprocess

import requests

import univention.testing.ucr as ucr_test
from univention.config_registry import handler_set
from univention.testing import utils

import samltest


def main():
    account = utils.UCSTestDomainAdminCredentials()
    supplement = 'second_eID'
    try:
        with ucr_test.UCSTestConfigRegistry() as ucr, samltest.GuaranteedIdP('127.0.0.1'):
            umc_saml_idpserver = ucr.get('umc/saml/idp-server')
            handler_set([f'saml/idp/entityID/supplement/{supplement}=true'])
            subprocess.check_call(['systemctl', 'restart', 'apache2.service'])
            saml_root = 'https://{}/simplesamlphp/{}/'.format(ucr.get('ucs/server/sso/fqdn'), supplement,)
            supplement_entityID = f'{saml_root}saml2/idp/metadata.php'
            print(f'supplement_entityID: "{supplement_entityID}"')
            handler_set([f'umc/saml/idp-server={supplement_entityID}'])
            metadata_req = requests.get(supplement_entityID)
            metadata_req.raise_for_status()
            if f'entityID="{supplement_entityID}"' not in metadata_req.text:
                print(f'IDP Metadata:\n{metadata_req.text}')
                utils.fail('entityID not changed?')
            SamlSession = samltest.SamlTest(account.username, account.bindpw,)
            try:
                SamlSession.login_with_new_session_at_IdP()
                SamlSession.test_logged_in_status()
                SamlSession.logout_at_IdP()
                SamlSession.test_logout_at_IdP()
                SamlSession.test_logout()
            except samltest.SamlError as exc:
                utils.fail(str(exc))
    finally:
        subprocess.check_call(['systemctl', 'reload', 'apache2.service'])
        if umc_saml_idpserver:
            subprocess.check_call(['ucr', 'set', f'umc/saml/idp-server={umc_saml_idpserver}'])


if __name__ == '__main__':
    main()
    print("####Success: SSO login is working####")
