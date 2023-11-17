#!/usr/share/ucs-test/runner python3
## desc: Check Docker App mod_proxy configuration
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

from univention.testing.ucr import UCSTestConfigRegistry

from dockertest import Appcenter, get_app_name, get_app_version, tiny_app_apache


if __name__ == '__main__':
    with Appcenter() as appcenter:
        # normal modproxy
        app_name = get_app_name()
        app_version = get_app_version()
        ucr = UCSTestConfigRegistry()

        app = tiny_app_apache(app_name, app_version)

        try:
            app.set_ini_parameter(
                WebInterface='/%s' % app.app_name,
                WebInterfacePortHTTP='80',
                WebInterfacePortHTTPS='443',
                AutoModProxy='True',
            )
            app.add_to_local_appcenter()

            appcenter.update()

            app.install()
            app.configure_tinyapp_modproxy()
            app.verify()

            app.verify_basic_modproxy_settings_tinyapp()
            ucr.load()
            assert ucr.get('ucs/web/overview/entries/service/%s/port_http' % app_name) == '80', ucr.get('ucs/web/overview/entries/service/%s/port_http' % app_name)
            assert ucr.get('ucs/web/overview/entries/service/%s/port_https' % app_name) == '443', ucr.get('ucs/web/overview/entries/service/%s/port_https' % app_name)

        finally:
            app.uninstall()
            app.remove()

        # special mod proxy with disabled HTTP
        app_version = get_app_version()

        app = tiny_app_apache(app_name, app_version)

        try:
            app.set_ini_parameter(
                WebInterface='/%s' % app.app_name,
                WebInterfacePortHTTP='0',  # NO HTTP!
                WebInterfacePortHTTPS='80',  # ONLY HTTPS PUBLICLY!
                WebInterfaceProxyScheme='http',  # CONTAINER ONLY HAS HTTP (80) SUPPORT!
                AutoModProxy='True',
            )

            app.add_to_local_appcenter()

            appcenter.update()

            app.install()
            app.configure_tinyapp_modproxy()
            app.verify()

            app.verify_basic_modproxy_settings_tinyapp(http=False, https=True)
            ucr.load()
            assert ucr.get('ucs/web/overview/entries/service/%s/port_http' % app_name) == '', ucr.get('ucs/web/overview/entries/service/%s/port_http' % app_name)
            assert ucr.get('ucs/web/overview/entries/service/%s/port_https' % app_name) == '443', ucr.get('ucs/web/overview/entries/service/%s/port_https' % app_name)

        finally:
            app.uninstall()
            app.remove()
