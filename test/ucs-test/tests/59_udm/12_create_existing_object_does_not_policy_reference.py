#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test that --policy-reference is not evaluated when creating a existing object
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## bugs: [38856]
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import pytest

import univention.testing.strings as uts
import univention.testing.udm as udm_test
import univention.testing.utils as utils


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_create_existing_object_does_not_policy_reference(udm):
	dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
	policy = udm.create_object('policies/pwhistory', **{'name': uts.random_string()})

	subnet_mask = '24'
	subnet = '10.20.30.0'
	dhcp_subnet = udm.create_object('dhcp/subnet', superordinate=dhcp_service, subnet=subnet, subnetmask=subnet_mask)
	with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
		dhcp_subnet = udm.create_object('dhcp/subnet', superordinate=dhcp_service, subnet=subnet, subnetmask=subnet_mask, policy_reference=policy)

	utils.verify_ldap_object(dhcp_subnet, {'univentionPolicyReference': []})
