#!/usr/share/ucs-test/runner python3
## desc: Create and install a simple docker app without the DockerImage parameter
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

from univention.testing.utils import fail, package_installed

from dockertest import App, Appcenter, get_app_name, get_app_version


if __name__ == '__main__':
    with Appcenter() as appcenter:
        app_name = get_app_name()
        app_version = get_app_version()

        app = App(name=app_name, version=app_version)

        try:
            # DockerImage is missing, this should not work
            app.set_ini_parameter()
            app.add_to_local_appcenter()

            appcenter.update()

            app.install()

            # The package must be installed locally
            if not package_installed(app.package_name):
                fail('The package %s is not installed locally.' % app.package_name)

        finally:
            app.uninstall()
            app.remove()
