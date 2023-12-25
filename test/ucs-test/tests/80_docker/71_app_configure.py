#!/usr/share/ucs-test/runner python3
## desc: Test the .configure script for Apps
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

from dockertest import Appcenter, get_app_name, get_app_version, tiny_app


if __name__ == '__main__':
    with Appcenter() as appcenter:
        app = tiny_app(get_app_name(), get_app_version())
        try:
            app.set_ini_parameter(
                DockerScriptConfigure='/tmp/configure',
                DockerScriptSetup='/tmp/setup')
            app.add_script(configure='''#!/bin/sh
set -x
echo "Configuring the App"
echo -n "$(more /etc/univention/base.conf | sed -ne 's|^test/configure/param: ||p')"  > /tmp/configure.output
exit 0
''')
            app.add_script(setup='#!/bin/sh')
            app.add_to_local_appcenter()
            appcenter.update()
            app.install()
            app.verify()
            configured_file = app.file('/tmp/configure.output')
            app.configure({'test/configure/param': 'test1'})
            assert open(configured_file).read() == 'test1'
            app.configure({'test/configure/param': 'test2'})
            assert open(configured_file).read() == 'test2'
            app.configure({'test/configure/param': None})
            assert open(configured_file).read() == ''
        finally:
            app.uninstall()
            app.remove()
