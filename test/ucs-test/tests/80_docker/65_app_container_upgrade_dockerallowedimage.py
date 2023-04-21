#!/usr/share/ucs-test/runner python3
## desc: Test DockerAllowedImages
## tags: [docker]
## exposure: dangerous
## versions:
##  4.1-0: skip
## packages:
##   - docker.io

from univention.config_registry import ConfigRegistry
from univention.testing.utils import fail, get_ldap_connection

from dockertest import App, Appcenter, get_app_name, get_docker_appbox_image, get_docker_appbox_ucs


if __name__ == '__main__':

    with Appcenter() as appcenter:
        appcenter.add_ucs_version_to_appcenter('4.0')

        app_name = get_app_name()
        package_name = get_app_name()

        # The UCS 4.0-3 image needs a 4.0-3 App Center
        app = App(name=app_name, version='1', package_name=package_name)
        app.ucs_version = '4.0'
        app.add_to_local_appcenter()
        app_directory_suffix = app.app_directory_suffix

        # Since we are installing on a 4.1, a 4.1 ini entry is needed
        app = App(name=app_name, version='1', container_version=get_docker_appbox_ucs(), package_name=package_name, build_package=False)
        app.set_ini_parameter(
            DockerImage='docker.software-univention.de/ucs-appbox-amd64:4.0-3',
            WebInterface='/%s' % app_name,
            WebInterfacePortHTTP='80',
            WebInterfacePortHTTPS='443',
            AutoModProxy='True',
            DockerScriptSetup='/usr/sbin/%s-setup' % app_name,
        )
        app.create_basic_modproxy_settings()

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
            print('Container UUID: %s' % container_uuid)

            app = App(name=app_name, version='2', container_version=get_docker_appbox_ucs(), package_name=package_name, app_directory_suffix=app_directory_suffix)
            app.set_ini_parameter(
                DockerImage=get_docker_appbox_image(),
                DockerAllowedImages='docker.software-univention.de/nonexisting-image1,docker.software-univention.de/ucs-appbox-amd64:4.0-3,docker.software-univention.de/nonexisting-image1',
                WebInterface='/%s' % app_name,
                WebInterfacePortHTTP='80',
                WebInterfacePortHTTPS='443',
                AutoModProxy='True',
                DockerScriptSetup='/usr/sbin/%s-setup' % app_name,
            )
            app.create_basic_modproxy_settings()

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
            if container_uuid != container_uuid_new:
                fail('The container UUID has been changed.')

        finally:
            app.uninstall()
            app.remove()
