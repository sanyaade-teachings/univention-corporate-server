#!/usr/share/ucs-test/runner pytest-3 -s -l -vv

## desc: Register UDM extension and perform simple LDAP verification
## tags: [udm,udm-extensions,apptest]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## exposure: dangerous
## packages:
##   - univention-config
##   - univention-directory-manager-tools
##   - shell-univention-lib

import bz2

import pytest

from univention.testing.debian_package import DebianPackage
from univention.testing.udm_extensions import (
	VALID_EXTENSION_TYPES, call_join_script, get_dn_of_extension_by_name, get_extension_buffer,
	get_extension_filename, get_extension_name, get_join_script_buffer, get_package_name,
	get_package_version, remove_extension_by_name,
)
from univention.testing.utils import verify_ldap_object, wait_for_replication


# make extension_type inheritable by other fixtures
@pytest.fixture
def extension_type(request):
	return request.param


@pytest.fixture
def package_and_extension(extension_type):
	package_name = get_package_name()
	package_version = get_package_version()
	extension_name = get_extension_name(extension_type)
	extension_filename = get_extension_filename(extension_type, extension_name)
	joinscript_buffer = get_join_script_buffer(
		extension_type,
		'/usr/share/%s/%s' % (package_name, extension_filename),
		version_start='5.0-0'
	)
	extension_buffer = get_extension_buffer(extension_type, extension_name)

	package = DebianPackage(name=package_name, version=package_version)

	yield package_name, package_version, extension_name, extension_filename, joinscript_buffer, extension_buffer, package

	print('Removing UDM extension from LDAP')
	remove_extension_by_name(extension_type, extension_name, fail_on_error=False)

	print('Uninstalling binary package %r' % package_name)
	package.uninstall()

	print('Removing source package')
	package.remove()


@pytest.mark.tags('udm', 'udm-extensions', 'apptest')
@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
@pytest.mark.exposure('dangerous')
@pytest.mark.parametrize('extension_type', VALID_EXTENSION_TYPES, indirect=True)
def test_register_and_verify_ldap_object(extension_type, package_and_extension):
	"""Register UDM extension and perform simple LDAP verification"""

	package_name, package_version, extension_name, extension_filename, joinscript_buffer, extension_buffer, package = package_and_extension

	print('========================= TESTING EXTENSION %s =============================' % extension_type)
	# create package and install it
	package.create_join_script_from_buffer('66%s.inst' % package_name, joinscript_buffer)
	package.create_usr_share_file_from_buffer(extension_filename, extension_buffer)
	package.build()
	package.install()

	call_join_script('66%s.inst' % package_name)

	# wait until removed object has been handled by the listener
	wait_for_replication()

	dnlist = get_dn_of_extension_by_name(extension_type, extension_name)
	assert dnlist, 'Cannot find UDM %s extension with name %s in LDAP' % (extension_type, extension_name)
	verify_ldap_object(dnlist[0], {
		'cn': [extension_name],
		'univentionUDM%sFilename' % extension_type.capitalize(): [extension_filename],
		'univentionOwnedByPackage': [package_name],
		'univentionObjectType': ['settings/udm_%s' % extension_type],
		'univentionOwnedByPackageVersion': [package_version],
		'univentionUDM%sData' % extension_type.capitalize(): [bz2.compress(extension_buffer.encode('UTF-8'))],
	})
