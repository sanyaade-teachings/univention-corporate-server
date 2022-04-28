#!/usr/share/ucs-test/runner python3
## desc: Test removing values from UCR policy
## bugs: [43562]
## roles:
##  - domaincontroller_master
## exposure: dangerous

from univention.testing import utils
from univention.testing.udm import UCSTestUDM


def main():
	with UCSTestUDM() as udm:
		policy = udm.create_object('policies/registry', name='test', registry=['foo bar', 'bar baz'])
		utils.verify_ldap_object(policy, {'univentionRegistry;entry-hex-666f6f': ['bar'], 'univentionRegistry;entry-hex-626172': ['baz']})
		udm.modify_object('policies/registry', dn=policy, remove={'registry': ['bar baz']})
		utils.verify_ldap_object(policy, {'univentionRegistry;entry-hex-666f6f': ['bar']})


if __name__ == '__main__':
	main()
