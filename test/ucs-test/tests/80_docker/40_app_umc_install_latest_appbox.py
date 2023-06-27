#!/usr/share/ucs-test/runner python3
## desc: Create and install a simple app with latest appbox image
## tags: [docker, SKIP]
## bugs: [51847]
## exposure: dangerous
## packages:
##   - docker.io

import json

import requests

from dockertest import App, Appcenter, UCTTest_DockerApp_UMCInstallFailed, get_app_name


if __name__ == '__main__':
    # get latest app box image
    url = 'https://docker.software-univention.de/v2/ucs-appbox-amd64/tags/list'
    username = 'ucs'
    password = 'readonly'
    resp = requests.get(url, auth=(username, password)).content
    data = json.loads(resp)
    image = 'docker.software-univention.de/ucs-appbox-amd64:' + max(data['tags'])

    # installation should fail if setup fails
    with Appcenter() as appcenter:
        app_name = get_app_name()
        app = App(name=app_name, version='1.9', container_version=max(data['tags'])[:3], build_package=False)
        app.set_ini_parameter(DockerImage=image, DockerScriptSetup='/usr/sbin/setup')
        app.add_script(setup='''#!/bin/bash
echo "This message goes to stdout"
echo "This message goes to stderr" >&2
. /usr/share/univention-docker-container-mode/lib.sh
error_msg "This message goes to ERROR_FILE"
exit 1
''')
        app.add_to_local_appcenter()
        appcenter.update()
        try:
            try:
                app.install_via_umc()
            except UCTTest_DockerApp_UMCInstallFailed as exc:
                progress, errors = exc.args
                print(errors)
                assert {'message': 'This message goes to ERROR_FILE\n', 'level': 'CRITICAL'} in errors
            else:
                raise AssertionError('Should not have been installed successfully!')
        finally:
            app.uninstall()
            app.remove()

    # installation should succeed if setup is fine
    with Appcenter() as appcenter:
        app_name = get_app_name()
        app = App(name=app_name, version='1.9', container_version=max(data['tags'])[:3], build_package=False)
        app.set_ini_parameter(DockerImage=image, DockerScriptSetup='/usr/sbin/setup')
        app.add_script(setup='''#!/bin/bash
echo "This message goes to stdout"
echo "This message goes to stderr but script returns 0" >&2
exit 0
''')
        app.add_to_local_appcenter()
        try:
            appcenter.update()
            app.install_via_umc()
        finally:
            app.uninstall()
            app.remove()

    # test appbox app installation
    with Appcenter() as appcenter:
        app_name = get_app_name()
        app_name = 'testapp'
        app = App(name=app_name, version='1.9', container_version=max(data['tags'])[:3], build_package=False)
        app.set_ini_parameter(
            DockerImage=image,
            DefaultPackages='mc',
        )
        app.add_to_local_appcenter()
        try:
            appcenter.update()
            app.install_via_umc()
            app.verify()
        finally:
            app.uninstall()
            app.remove()
