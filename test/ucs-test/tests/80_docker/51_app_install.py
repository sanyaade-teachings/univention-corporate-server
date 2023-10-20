#!/usr/share/ucs-test/runner python3
## desc: Create and install a simple docker app
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

from univention.testing.utils import get_ldap_connection

from dockertest import Appcenter, get_app_name, get_app_version, tiny_app


if __name__ == '__main__':

    with Appcenter() as appcenter:
        app_name = get_app_name()
        app_version = get_app_version()

        app = tiny_app(app_name, app_version)
        try:
            app.add_to_local_appcenter()

            appcenter.update()

            app.install()

            app.verify(joined=False)

            lo = get_ldap_connection()
            print(lo.searchDn(filter='(&(cn=%s-*)(objectClass=univentionMemberServer)(!(aRecord=*))(!(macAddress=*)))' % app_name[:5], unique=True, required=True))
        finally:
            app.uninstall()
            app.remove()
