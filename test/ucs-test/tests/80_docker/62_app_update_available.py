#!/usr/share/ucs-test/runner python3
## desc: Test the update_available script
## tags: [docker, SKIP]
## exposure: dangerous
## packages:
##   - docker.io

# skipped until we have 4.3-4 or 4.4-1 appbox

from univention.config_registry import ConfigRegistry
from univention.testing.debian_package import DebianPackage
from univention.testing.utils import UCSTestDomainAdminCredentials, fail, get_ldap_connection

from dockertest import (
    App, Appcenter, copy_package_to_appcenter, get_app_name, get_docker_appbox_image, get_docker_appbox_ucs,
)


if __name__ == '__main__':

    with Appcenter() as appcenter:

        ucr = ConfigRegistry()
        ucr.load()

        app_name = get_app_name()
        package_name = get_app_name()

        app = App(name=app_name, version='1', container_version=get_docker_appbox_ucs(), package_name=package_name)
        app.set_ini_parameter(DockerImage=get_docker_appbox_image())

        app.add_to_local_appcenter()

        package_name = get_app_name()
        test_package_v1 = DebianPackage(name=package_name, version='0.1')
        test_package_v1.build()
        copy_package_to_appcenter(get_docker_appbox_ucs(), app.app_directory, test_package_v1.get_binary_name())

        admin_credentials = UCSTestDomainAdminCredentials()

        try:

            appcenter.update()

            app.install()
            app.verify()

            lo = get_ldap_connection()
            print(lo.searchDn(filter='(&(cn=%s-*)(objectClass=univentionMemberServer))' % app_name[:5], unique=True, required=True))
            app.execute_command_in_container('univention-upgrade --noninteractive --updateto=%s-99 --disable-app-updates' % ucr['version/version'])

            app.execute_command_in_container('univention-install %s' % package_name)
            app.execute_command_in_container('bash -c "echo -n \"%s\" >/.pwd"' % admin_credentials.bindpw)
            app.execute_command_in_container('univention-run-join-scripts -dcaccount "%s" -dcpwd "/.pwd"' % admin_credentials.username)
            app.execute_command_in_container('/usr/share/univention-updater/univention-updater-check')
            res = app.execute_command_in_container('/usr/share/univention-docker-container-mode/update_available')
            if 'packages' in res:
                fail('update_available returned [%s]' % res)

            test_package_v2 = DebianPackage(name=package_name, version='0.2')
            test_package_v2.build()
            copy_package_to_appcenter(get_docker_appbox_ucs(), app.app_directory, test_package_v2.get_binary_name())
            app.execute_command_in_container('/usr/share/univention-updater/univention-updater-check')
            app.execute_command_in_container('ucr unset update/container/check/type update/container/check/last')
            res = app.execute_command_in_container('/usr/share/univention-docker-container-mode/update_available')
            if 'packages' not in res:
                fail('update_available returned [%s] instead of [packages\n]' % res)

            app.execute_command_in_container('ucr set version/version=4.0 version/patchlevel=12')
            app.execute_command_in_container('/usr/share/univention-updater/univention-updater-check')
            app.execute_command_in_container('ucr unset update/container/check/type update/container/check/last')
            res = app.execute_command_in_container('/usr/share/univention-docker-container-mode/update_available')
            if res != 'release: 4.1-0\n':
                fail('update_available returned [%s] instead of [release: 4.1-0\n]' % res)

        finally:
            app.uninstall()
            app.remove()
