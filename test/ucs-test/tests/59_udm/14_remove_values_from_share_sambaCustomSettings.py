#!/usr/share/ucs-test/runner python3
## desc: Test removing values from share
## bugs: [41072]
## roles:
##  - domaincontroller_master
## tags: [apptest]
## exposure: dangerous

from univention.testing import utils
from univention.testing.udm import UCSTestUDM


def main():
	with UCSTestUDM() as udm:
		share = udm.create_object('shares/share', name='test', host='localhost', path='/path/', sambaCustomSettings='"follow symlinks" "yes"')
		utils.verify_ldap_object(share, {'univentionShareSambaCustomSetting': ['follow symlinks = yes']})
		udm.modify_object('shares/share', dn=share, remove={'sambaCustomSettings': ['"follow symlinks" "yes"']})
		utils.verify_ldap_object(share, {'univentionShareSambaCustomSetting': []})


if __name__ == '__main__':
	main()
