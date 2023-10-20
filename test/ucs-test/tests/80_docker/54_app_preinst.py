#!/usr/share/ucs-test/runner python3
## desc: Check the preinst script
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import subprocess

from dockertest import (
    Appcenter, UCSTest_DockerApp_InstallationFailed, UCSTest_DockerApp_VerifyFailed, get_app_name, get_app_version,
    tiny_app,
)


def create_app(fail_in_preinst):
    app_name = get_app_name()
    app_version = get_app_version()

    app = tiny_app(app_name, app_version)
    try:
        app.add_script(preinst='''#!/bin/bash
set -x -e
echo "Test preinst script"
if [ "%(exit_code)d" = "0" ]; then
    ucr set appcenter/apps/%(app_name)s/docker/params="-e FOO=bar -e repository_app_center_server=my.server"
fi
exit %(exit_code)d
''' % {'exit_code': (1 if fail_in_preinst else 0), 'app_name': app_name})

        app.add_to_local_appcenter()

        appcenter.update()

        try:
            app.install()
            app.verify(joined=False)
        except (UCSTest_DockerApp_VerifyFailed, UCSTest_DockerApp_InstallationFailed):
            if not fail_in_preinst:
                raise
        else:
            if fail_in_preinst:
                raise ValueError('Should not have been installed!')
            else:
                output = subprocess.check_output('univention-app shell %s env' % app_name, shell=True, text=True)
                if 'FOO=bar' not in output or 'repository_app_center_server=my.server' not in output:
                    raise ValueError('Setting docker/params does not work')

    finally:
        app.uninstall()
        app.remove()


if __name__ == '__main__':
    with Appcenter() as appcenter:
        create_app(fail_in_preinst=False)
        create_app(fail_in_preinst=True)
