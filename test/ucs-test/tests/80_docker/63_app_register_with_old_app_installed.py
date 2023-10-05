#!/usr/share/ucs-test/runner python3
## desc: Test univention-app register with an old app installed
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

from dockertest import App, Appcenter


if __name__ == '__main__':
    with Appcenter() as appcenter:
        try:
            name = "my-test-app"
            setup = '#!/bin/sh'
            store_data = '#!/bin/sh'

            # install the old version
            old_app = App(name=name, version='1', build_package=False, call_join_scripts=False, container_version="5.1")
            old_app.set_ini_parameter(
                DockerImage='docker-test.software-univention.de/alpine:3.6',
                DockerScriptSetup='/setup',
                DockerScriptStoreData='/store_data',
                DockerScriptInit='/sbin/init',
            )
            old_app.add_script(setup=setup)
            old_app.add_script(store_data=store_data)
            old_app.add_to_local_appcenter()
            appcenter.update()
            old_app.install()
            old_app.verify(joined=False)

            # create a new version
            new_app = App(name=name, version='2', build_package=False, call_join_scripts=False)
            new_app.set_ini_parameter(
                DockerImage='docker-test.software-univention.de/alpine:3.7',
                DockerScriptSetup='/setup',
                DockerScriptStoreData='/store_data',
                DockerScriptInit='/sbin/init',
            )
            new_app.add_script(setup=setup)
            new_app.add_script(store_data=store_data)
            new_app.add_to_local_appcenter()
            appcenter.update()

            # run register
            old_app.register()
            old_app.verify(joined=False)
        finally:
            old_app.uninstall()
            old_app.remove()
