#!/usr/share/ucs-test/runner python3
## desc: Create and install a simple docker app
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import pytest

from dockertest import App, Appcenter, UCSTest_DockerApp_InstallationFailed, get_app_name, get_app_version


if __name__ == '__main__':
    with Appcenter() as appcenter:
        app_name = get_app_name()
        app_version = get_app_version()
        app = App(name=app_name, version=app_version, container_version='5.0', build_package=False,)

        try:
            app.set_ini_parameter(DefaultPackages='foobar')
            app.add_to_local_appcenter()

            appcenter.update()

            with pytest.raises(UCSTest_DockerApp_InstallationFailed):
                app.install()
        finally:
            app.uninstall()
            app.remove()
