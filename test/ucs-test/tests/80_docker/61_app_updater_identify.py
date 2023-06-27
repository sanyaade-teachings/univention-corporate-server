#!/usr/share/ucs-test/runner python3
## desc: Check updater/identify in a new Docker App
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

from dockertest import (
    App, Appcenter, UCSTest_Docker_Exception, get_app_name, get_app_version, get_docker_appbox_image,
    get_docker_appbox_ucs,
)


class UCSTest_DockerApp_Identify(UCSTest_Docker_Exception):
    pass


if __name__ == '__main__':

    with Appcenter() as appcenter:
        app_name = get_app_name()
        app_version = get_app_version()

        app = App(name=app_name, version=app_version, container_version=get_docker_appbox_ucs())

        try:
            app.set_ini_parameter(DockerImage=get_docker_appbox_image())
            app.add_to_local_appcenter()

            appcenter.update()

            app.install()

            app.verify()

            identify = app.execute_command_in_container('ucr get updater/identify')
            print('Identify: %s' % identify)
            if identify.strip() != 'Docker App':
                raise UCSTest_DockerApp_Identify()

        finally:
            app.uninstall()
            app.remove()
