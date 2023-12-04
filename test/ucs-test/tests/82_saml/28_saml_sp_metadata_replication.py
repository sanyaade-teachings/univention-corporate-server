#!/usr/share/ucs-test/runner python3
## desc: Check service provider metadata replication.
## tags:
##  - saml
## bugs: [47309]
## roles: [domaincontroller_master, domaincontroller_backup]
## join: true
## exposure: dangerous

import difflib
import os.path
import subprocess

import univention.admin.modules as udm_modules
import univention.config_registry as configRegistry
import univention.testing.udm as udm_test
from univention.testing import utils

import samltest


ucr = configRegistry.ConfigRegistry()
ucr.load()
udm_modules.update()


class ListenerError(Exception):
    pass


def main():
    account = utils.UCSTestDomainAdminCredentials()
    saml_session = samltest.SamlTest(account.username, account.bindpw)
    lo = utils.get_ldap_connection(admin_uldap=True)
    master = udm_modules.lookup('computers/domaincontroller_master', None, lo, scope='sub')
    master_hostname = "%s.%s" % (master[0]['name'], master[0]['domain'])
    cmd_disable = [
        '/usr/sbin/udm', 'saml/serviceprovider', 'modify',
        '--dn=SAMLServiceProviderIdentifier=https://%s/univention/saml/metadata,cn=saml-serviceprovider,cn=univention,%s' % (master_hostname, ucr.get('ldap/base')),
        '--set', 'isActivated=FALSE',
    ]
    cmd_enable = [
        '/usr/sbin/udm', 'saml/serviceprovider', 'modify',
        '--dn=SAMLServiceProviderIdentifier=https://%s/univention/saml/metadata,cn=saml-serviceprovider,cn=univention,%s' % (master_hostname, ucr.get('ldap/base')),
        '--set', 'isActivated=TRUE',
    ]
    # Force update of the sp config to avoid test failures due to old configs
    subprocess.check_call(cmd_disable)
    utils.wait_for_replication()
    subprocess.check_call(cmd_enable)
    utils.wait_for_replication()

    try:
        # Copy service provider config from UMC, delete it, and re-inject it as a new service provider
        # using the functionality introduced in Bug #47309
        metadata_filename = f'/usr/share/univention-management-console/saml/idp/ucs-sso-ng.{ucr["domainname"]}.xml'
        with open(metadata_filename) as metadata_file:
            metadata = metadata_file.read()

        # set udm saml/sp object to 'deactivated' so the file is removed
        subprocess.check_call(cmd_disable)
        utils.wait_for_replication()
        # if os.path.exists(metadata_filename):
        #     raise ListenerError('Metadata was not deleted by the listener!')
        try:
            with samltest.GuaranteedIdP('127.0.0.1'):
                # Use the local IdP server, that way we don't need to wait for domain wide replication.
                saml_session.target_sp_hostname = master_hostname
                saml_session.login_with_new_session_at_IdP()
                saml_session.test_logged_in_status()
        except samltest.SamlError as exc:
            expected_error = "<h2>Metadata not found</h2>"
            if expected_error not in str(exc):
                utils.fail("Login failed, but for the wrong reason?:\n%s" % str(exc))
        else:
            utils.fail("Serviceprovider deactivation failed")

        # add new SP with raw metadata
        with udm_test.UCSTestUDM() as udm:
            new_identifier = 'ucs-test-sp'
            new_service_provider = {'Identifier': new_identifier, 'isActivated': 'TRUE', 'AssertionConsumerService': 'https://.de', 'rawsimplesamlSPconfig': metadata}
            udm.create_object('saml/serviceprovider', **new_service_provider)

            utils.wait_for_replication()
            if not os.path.exists(f'/etc/simplesamlphp/metadata.d/{new_identifier}.php'):
                raise ListenerError('Metadata was not written by the listener!')
            # try to login
            with samltest.GuaranteedIdP('127.0.0.1'):
                saml_session.target_sp_hostname = master_hostname
                saml_session.login_with_new_session_at_IdP()
                saml_session.test_logged_in_status()
    except samltest.SamlError as exc:
        utils.fail(str(exc))
    finally:
        # enable SP config in any case to reset state
        subprocess.check_call(cmd_enable)
        utils.wait_for_replication()
        if not os.path.exists(metadata_filename):
            raise ListenerError('Metadata was not written by the listener!')
        with open(metadata_filename) as metadata_file:
            metadata_new = metadata_file.read()
        if metadata_new != metadata:
            print(f'old: {metadata}')
            print(f'new: {metadata_new}')
            print('##########################')
            print('{}'.format('\n'.join(difflib.unified_diff(
                metadata.splitlines(),
                metadata_new.splitlines(),
                fromfile='old metadata',
                tofile='new metadata',
            ))))
            raise ListenerError('Metadata written by the listener differs from old metadata!')


if __name__ == '__main__':
    main()
