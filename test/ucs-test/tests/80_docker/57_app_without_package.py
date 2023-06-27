#!/usr/share/ucs-test/runner python3
## desc: Create and install a simple docker app without a Debian package (plain container app)
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

from univention.testing.utils import get_ldap_connection

from dockertest import App, Appcenter, get_app_name, get_app_version, get_docker_appbox_image, get_docker_appbox_ucs


if __name__ == '__main__':

    with Appcenter() as appcenter:
        app_name = get_app_name()
        app_version = get_app_version()

        app = App(name=app_name, version=app_version, container_version=get_docker_appbox_ucs(), build_package=False)

        try:
            app.set_ini_parameter(
                DockerImage=get_docker_appbox_image(),
                WebInterface='/%s' % app.app_name,
                WebInterfacePortHTTP='80',
                WebInterfacePortHTTPS='443',
                AutoModProxy='True',
                DockerScriptSetup='/usr/sbin/%s-setup' % app_name,
            )
            app.create_basic_modproxy_settings()
            app.add_to_local_appcenter()

            appcenter.update()

            app.install()

            app.verify()

            app.verify_basic_modproxy_settings()

            lo = get_ldap_connection()
            print(lo.searchDn(filter='(&(cn=%s-*)(objectClass=univentionMemberServer)(!(aRecord=*))(!(macAddress=*)))' % app_name[:5], unique=True, required=True))
        finally:
            app.uninstall()
            app.remove()
