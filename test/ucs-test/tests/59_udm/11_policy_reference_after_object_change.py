#!/usr/share/ucs-test/runner python3
## desc: policy reference works after changing the objects dn
## tags: [udm,apptest,SKIP]
## roles: [domaincontroller_master]
## bugs: [41694]
## exposure: dangerous
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import univention.testing.udm as udm_test
import univention.testing.utils as utils
from univention.testing.strings import random_string

if __name__ == '__main__':
	with udm_test.UCSTestUDM() as udm:
		for object_type in ('container/cn', 'mail/domain'):
			print('testing', object_type)
			policy = udm.create_object('policies/pwhistory', **{'name': random_string()})
			old_dn = udm.create_object(object_type, **{'name': random_string()})

			new_dn = udm.modify_object(object_type, **{'name': random_string(), 'dn': old_dn, 'policy_reference': policy})
			print('new_dn', new_dn)
			utils.verify_ldap_object(new_dn, {'univentionPolicyReference': [policy]})
			print('old_dn', old_dn)
			utils.verify_ldap_object(old_dn, should_exist=False)
