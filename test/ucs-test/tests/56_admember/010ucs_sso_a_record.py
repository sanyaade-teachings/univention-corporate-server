#!/usr/share/ucs-test/runner python3
## desc: Check ucs-sso A record on AD server
## tags: [admember]
## exposure: safe
## packages: [univention-samba]
## roles: [domaincontroller_master,domaincontroller_backup]
## bugs: [39574]

import sys

import dns.resolver

import univention.lib.admember
from univention.config_registry.interfaces import Interfaces
from univention.testing.codes import TestCodes


if not univention.lib.admember.is_localhost_in_admember_mode():
    sys.exit(TestCodes.RESULT_SKIP)

ucr = univention.config_registry.ConfigRegistry()
ucr.load()
ad_domain_info = univention.lib.admember.lookup_adds_dc()
ad_ip = ad_domain_info['DC IP']
my_ip = Interfaces().get_default_ip_address().ip
domainname = ucr.get('domainname')
fqdn = ucr.get('ucs/server/sso/fqdn', 'ucs-sso.' + domainname)

resolver = dns.resolver.Resolver()
resolver.nameservers = [ad_ip]
resolver.lifetime = 10
response = resolver.query(fqdn, 'A')
ret_val = TestCodes.RESULT_FAIL
found = False
for data in response:
    if str(data) == str(my_ip):
        ret_val = TestCodes.RESULT_OKAY

sys.exit(ret_val)
