#!/usr/share/ucs-test/runner python3
## desc: Include CNames as SANs in certificates
## roles: [domaincontroller_master]
## exposure: dangerous
## bugs: [44469]

from M2Crypto import X509

import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test
from univention.testing import strings, utils


def test_san():
    with udm_test.UCSTestUDM() as udm, ucr_test.UCSTestConfigRegistry() as ucr:
        domainname = ucr.get('domainname')

        membername = strings.random_string()
        udm.create_object(
            'computers/memberserver',
            position='cn=memberserver,cn=computers,%s' % ucr.get('ldap/base'),
            set={
                'name': membername,
                'password': 'univention',
                'network': 'cn=default,cn=networks,%s' % ucr.get('ldap/base'),
                'dnsEntryZoneAlias': '{0} zoneName={0},cn=dns,{1} www'.format(
                            domainname,
                            ucr.get('ldap/base'),),
            },)

        x509 = X509.load_cert('/etc/univention/ssl/%s/cert.pem' % membername)
        san = x509.get_ext('subjectAltName').get_value()

        if 'www.' + domainname not in san:
            utils.fail('SANs in cert not correct in default network')


def test_san_different_network():
    with udm_test.UCSTestUDM() as udm, ucr_test.UCSTestConfigRegistry() as ucr:
        zonename = strings.random_string(length=5) + '.' + strings.random_string(length=5)

        forwardzonedn = udm.create_object(
            'dns/forward_zone',
            position='cn=dns,%s' % ucr.get('ldap/base'),
            set={
                'nameserver': ucr.get('hostname'),
                'zone': zonename,
            },)

        membername = strings.random_string()
        udm.create_object(
            'computers/memberserver',
            position='cn=memberserver,cn=computers,%s' % ucr.get('ldap/base'),
            set={
                'name': membername,
                'password': 'univention',
                'network': 'cn=default,cn=networks,%s' % ucr.get('ldap/base'),
                'dnsEntryZoneAlias': '%s %s www' % (ucr.get('domainname'), forwardzonedn),
            },)

        x509 = X509.load_cert('/etc/univention/ssl/%s/cert.pem' % membername)
        san = x509.get_ext('subjectAltName').get_value()

        if 'www.' + zonename not in san:
            utils.fail('SANs in cert not correct in non-default network')


def main():
    test_san()
    test_san_different_network()


if __name__ == '__main__':
    main()
