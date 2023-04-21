#!/usr/share/ucs-test/runner python3
## desc: Test the container upgrade without a re-join
## tags: [docker, SKIP]
## roles:
##  - domaincontroller_master
## exposure: dangerous
## packages:
##   - docker.io

from univention.config_registry import ConfigRegistry
from univention.testing.utils import fail, get_ldap_connection

from dockertest import App, Appcenter, get_app_name, get_docker_appbox_image, store_data_script_4_1


if __name__ == '__main__':
    with Appcenter() as appcenter:
        app_name = get_app_name()
        package_name = get_app_name()

        # Since we are installing on a 4.1, a 4.1 ini entry is needed
        app = App(name=app_name, version='1', container_version='4.1', package_name=package_name, build_package=False)
        app.set_ini_parameter(
            DockerImage='docker.software-univention.de/ucs-appbox-amd64:4.1-4',
            WebInterface='/%s' % app_name,
            WebInterfacePortHTTP='80',
            WebInterfacePortHTTPS='443',
            SupportedUCSVersions='4.1-0, 4.2-0, 4.3-0, 4.4-0',
            AutoModProxy='True',
            DockerScriptSetup='/usr/sbin/%s-setup' % app_name,
            DockerScriptStoreData='/usr/share/univention-appcenter/app/%s/store_data' % app_name,
        )
        app.create_basic_modproxy_settings()
        app.add_script(store_data=store_data_script_4_1())

        app.add_to_local_appcenter()

        try:
            appcenter.update()

            app.install()
            app.verify()

            app.verify_basic_modproxy_settings()

            lo = get_ldap_connection()
            print(lo.searchDn(filter='(&(cn=%s-*)(objectClass=univentionMemberServer))' % app_name[:5], unique=True, required=True))

            ucr = ConfigRegistry()
            ucr.load()
            container_uuid = ucr.get('appcenter/apps/%s/container' % app_name)
            machine_secret = app.execute_command_in_container('cat /etc/machine.secret')
            version_version = app.execute_command_in_container('ucr get version/version')
            app.execute_command_in_container('ln -sf /etc/machine.secret /etc/test.secret')
            test_secret = app.execute_command_in_container('test -L /etc/test.secret; echo $?')
            app.execute_command_in_container('ucr set test1=test123')
            ucr_test = app.execute_command_in_container('ucr get test1')

            # app = App(name=app_name, version='2', package_name=package_name, app_directory_suffix=app_directory_suffix)
            app = App(name=app_name, version='2', container_version='4.3', package_name=package_name)
            app.set_ini_parameter(
                DockerImage=get_docker_appbox_image(),
                WebInterface='/%s' % app_name,
                WebInterfacePortHTTP='80',
                WebInterfacePortHTTPS='443',
                AutoModProxy='True',
                SupportedUCSVersions='4.1-0, 4.2-0, 4.3-0, 4.4-0',
                DockerScriptSetup='/usr/sbin/%s-setup' % app_name,
                # For debugging and testing of store_data and restore_data
                # DockerScriptStoreData='/usr/share/univention-appcenter/app/%s/store_data' % app_name,
                # DockerScriptRestoreDataBeforeSetup='/usr/share/univention-appcenter/app/%s/restore_data_before_setup' % app_name,
            )
            app.create_basic_modproxy_settings()
            # For debugging and testing of store_data and restore_data
            # app.add_script(store_data=store_data_script_4_1())
            # app.add_script(restore_data_before_setup=restore_data_script_4_1())

            app.add_to_local_appcenter()

            appcenter.update()

            app.upgrade()
            app.verify()

            app.verify_basic_modproxy_settings()

            lo = get_ldap_connection()
            print(lo.searchDn(filter='(&(cn=%s-*)(objectClass=univentionMemberServer))' % app_name[:5], unique=True, required=True))

            ucr.load()
            container_uuid_new = ucr.get('appcenter/apps/%s/container' % app_name)
            print('Container UUID: %s' % container_uuid_new)
            if container_uuid == container_uuid_new:
                fail('The container UUID has not been changed.')
            machine_secret_new = app.execute_command_in_container('cat /etc/machine.secret')
            version_version_new = app.execute_command_in_container('ucr get version/version')
            ucr_test_new = app.execute_command_in_container('ucr get test1')
            test_secret_new = app.execute_command_in_container('test -L /etc/test.secret; echo $?')

            if machine_secret != machine_secret_new:
                fail('machine.secret has been changed')
            if version_version.strip() != '4.1':
                fail('old container was not 4.1')
            if version_version_new.strip() != '4.3':
                fail('new container was not 4.3')
            if ucr_test != ucr_test_new:
                fail('UCR variable test1 differes')
            if test_secret != test_secret_new:
                fail('/etc/test.secret link has been changed')

        finally:
            app.uninstall()
            app.remove()
