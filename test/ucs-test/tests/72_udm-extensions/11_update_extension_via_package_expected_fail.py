#!/usr/share/ucs-test/runner python3
## desc: Test extension update with wrong version order
## tags: [udm,udm-extensions,apptest]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## exposure: dangerous
## packages:
##   - univention-config
##   - univention-directory-manager-tools
##   - shell-univention-lib

import random

from univention.testing.debian_package import DebianPackage
from univention.testing.strings import random_name, random_version
from univention.testing.udm_extensions import (
	VALID_EXTENSION_TYPES, call_join_script, get_absolute_extension_filename, get_extension_buffer,
	get_extension_filename, get_extension_name, get_join_script_buffer, get_package_name,
	remove_extension_by_name,
)
from univention.testing.utils import fail, wait_for_replication


def test_extension(extension_type):
	package_name = get_package_name()
	version = random_version()
	package_version_LOW = '%s.%d' % (version, random.randint(0, 4))
	package_version_HIGH = '%s.%d' % (version, random.randint(5, 9))
	extension_name = get_extension_name(extension_type)
	extension_filename = get_extension_filename(extension_type, extension_name)
	app_id = '%s-%s' % (random_name(), random_version())
	joinscript_version = 1

	packages = []
	try:
		for package_version in (package_version_HIGH, package_version_LOW):
			# create unique extension identifier
			extension_identifier = '%s_%s' % (extension_name, package_version.replace('.', '_'))
			extension_buffer = get_extension_buffer(extension_type, extension_name, extension_identifier)
			joinscript_buffer = get_join_script_buffer(
				extension_type,
				'/usr/share/%s/%s' % (package_name, extension_filename),
				app_id=app_id,
				joinscript_version=joinscript_version,
				version_start='5.0-0'
			)
			joinscript_version += 1

			# create package and install it
			package = DebianPackage(name=package_name, version=package_version)
			packages.append(package)
			package.create_join_script_from_buffer('66%s.inst' % package_name, joinscript_buffer)
			package.create_usr_share_file_from_buffer(extension_filename, extension_buffer)
			package.build()
			package.install()

			exitcode = call_join_script('66%s.inst' % package_name, fail_on_error=False)
			if package_version == package_version_HIGH:
				if exitcode:
					fail('The join script failed with exitcode %s' % exitcode)
			else:
				if not exitcode:
					print('\nWARNING: a failure of the joinscript has been expected but in ran through\n')

			# wait until removed object has been handled by the listener
			wait_for_replication()

			content = open(get_absolute_extension_filename(extension_type, extension_filename)).read()
			if package_version == package_version_HIGH and extension_identifier not in content:
				fail('ERROR: UDM extension of package %d has not been written to disk (%s)' % (len(packages), extension_filename,))
			if package_version == package_version_LOW and extension_identifier in content:
				fail('ERROR: the extension update has been performed but should not (old version=%s ; new version=%s)' % (package_version_HIGH, package_version_LOW))

	finally:
		print('Removing UDM extension from LDAP')
		remove_extension_by_name(extension_type, extension_name, fail_on_error=False)

		for package in packages:
			print('Uninstalling binary package %r' % package.get_package_name())
			package.uninstall()

		print('Removing source package')
		for package in packages:
			package.remove()


if __name__ == '__main__':
	for extension_type in VALID_EXTENSION_TYPES:
		print('========================= TESTING EXTENSION %s =============================' % extension_type)
		test_extension(extension_type)
