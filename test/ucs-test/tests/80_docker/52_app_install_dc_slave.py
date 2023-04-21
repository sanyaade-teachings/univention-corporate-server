#!/usr/share/ucs-test/runner python3
## desc: Create and install a simple DC Slave docker app
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io
## versions:
##  4.1-0: skip
## bugs:
##  - 39792
##  - 39801

import time

import ldap

from univention.testing.utils import get_ldap_connection

from dockertest import App, Appcenter, get_app_name, get_app_version, get_docker_appbox_image, get_docker_appbox_ucs


if __name__ == '__main__':

    with Appcenter() as appcenter:
        app_name = get_app_name()
        app_version = get_app_version()

        app = App(name=app_name, version=app_version, container_version=get_docker_appbox_ucs())

        try:
            app.set_ini_parameter(DockerImage=get_docker_appbox_image(), DockerServerRole='domaincontroller_slave', DockerScriptSetup='/usr/sbin/%s-setup' % app_name)
            app.add_script(setup='''#!/bin/bash
set -x -e
univention-install --yes --no-install-recommends univention-server-slave univention-server-member-
/usr/share/univention-docker-container-mode/setup "$@"
''')

            app.add_to_local_appcenter()

            appcenter.update()

            app.install()

            app.verify()

            try:
                lo = get_ldap_connection()
            except ldap.SERVER_DOWN():
                print('LDAP connection failed. Wait for ten seconds and try again.')
                time.sleep(60)
                lo = get_ldap_connection()

            print(lo.searchDn(filter='(&(cn=%s-*)(objectClass=univentionDomainController)(univentionServerRole=slave)(!(aRecord=*)))' % app_name[:5], unique=True, required=True))

        finally:
            app.uninstall()
            app.remove()
