#!/usr/share/ucs-test/runner python3
## desc: Check if every DC Master and DC Backup is registered in ucs-sso
## tags: [saml]
## exposure: safe
## packages:
##   - univention-saml

import dns.ipv6
import dns.resolver

import univention.testing.ucr as ucr_test
from univention.testing.utils import fail, get_ldap_connection


def _check_record_type(record_type):
    print(f'Checking record type: {record_type}')
    dns_entries = set()
    try:
        for addr in dns.resolver.query('ucs-sso.%s' % ucr.get('domainname'), record_type):
            dns_entries.add(addr.address)
    except dns.resolver.NoAnswer:
        pass
    print(f'DNS entries: {"; ".join(dns_entries)}')

    master_backup_ips = set()
    lo = get_ldap_connection()
    ldap_record_name = {'A': 'aRecord', 'AAAA': 'aAAARecord'}
    ldap_filter = '(|(univentionServerRole=master)(univentionServerRole=backup))'
    for res in lo.search(ldap_filter, attr=[ldap_record_name[record_type]]):
        if res[1]:
            for ip in res[1].get(ldap_record_name[record_type]):
                if record_type == 'AAAA':
                    ip = dns.ipv6.inet_ntoa(dns.ipv6.inet_aton(ip))
                master_backup_ips.add(ip.decode('ASCII'))
    print(f'LDAP entries: {"; ".join(master_backup_ips)}')

    if master_backup_ips.difference(dns_entries):
        fail('Not all master and backup IPs are registered: DNS: [%s], LDAP: [%s]' % (dns_entries, master_backup_ips))
    return len(dns_entries)


if __name__ == '__main__':
    ucr = ucr_test.UCSTestConfigRegistry()
    ucr.load()

    number_of_records = 0
    for record_type in ('A', 'AAAA'):
        number_of_records += _check_record_type(record_type)

    if number_of_records == 0:
        fail('No dns record for ucs-sso')
    print('Success')
