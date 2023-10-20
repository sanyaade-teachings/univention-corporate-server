#!/usr/share/ucs-test/runner python3
## desc: Test ucr template mechanism for Docker apps
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import json
import subprocess

from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.utils import fail

from dockertest import Appcenter, get_app_name, get_app_version, tiny_app


def check_docker_arg_against_ucrv(container_id, ucrv):
    docker_inspect = subprocess.check_output(["docker", "inspect", f"{container_id}"], close_fds=True)
    args = json.loads(docker_inspect)[0]['Args']
    first_arg = args[0].split("=", 1)[1]
    if first_arg != ucrv:
        fail(f'\nThe container argument is not equal to the ucr variable it is checked against.\nDocker container argument: {first_arg}\nUCRV: {ucrv}\n')


if __name__ == '__main__':
    with Appcenter() as appcenter, UCSTestConfigRegistry() as ucr:
        ucr.load()
        app = tiny_app(get_app_name(), get_app_version())
        try:
            app.set_ini_parameter(
                DockerScriptSetup='/tmp/setup',
                DockerScriptInit='/sbin/init --test=@%@ldap/base@%@',
            )
            app.add_script(setup='#!/bin/sh')
            app.add_to_local_appcenter()
            appcenter.update()
            app.install()
            app.verify(joined=False)
            check_docker_arg_against_ucrv(app.container_id, ucr.get('ldap/base'))
        finally:
            try:
                app.uninstall()
            except Exception:
                fail('Could not uninstall app. Trying to remove..')
            app.remove()
