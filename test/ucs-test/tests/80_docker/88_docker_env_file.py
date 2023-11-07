#!/usr/share/ucs-test/runner python3
## desc: Test docker compose - with env file
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import subprocess

from univention.config_registry import ConfigRegistry

from dockertest import App, Appcenter, get_app_name


DOCKER_COMPOSE = '''
version: '2.0'

services:
    test1:
        image: {image}
        command: /sbin/init
        restart: always
    test2:
        image: {image}
        command: /sbin/init
        restart: always
'''.replace('\t', '  ')

ENV = '''
REDIS_PORT_6379_TCP_ADDR=test2
REDIS_PORT_6379_TCP_PORTc=6379
TEST_HOSTNAME=@%@hostname@%@
'''

if __name__ == '__main__':
    with Appcenter() as appcenter:

        name = get_app_name()
        setup = '#!/bin/sh'
        store_data = '#!/bin/sh'

        app = App(name=name, version='1', build_package=False, call_join_scripts=False)
        try:
            app.set_ini_parameter(
                DockerMainService='test1',
                DockerInjectEnvFile='main',
            )
            app.add_script(compose=DOCKER_COMPOSE.format(image='docker-test.software-univention.de/alpine:3.6'))
            app.add_script(env=ENV)
            app.add_script(setup=setup)
            app.add_script(store_data=store_data)
            app.add_to_local_appcenter()
            appcenter.update()
            app.install()
            app.verify()
            env_file = '/var/lib/univention-appcenter/apps/%s/compose/%s.env' % (name, name)
            subprocess.call(['ls', '-la', env_file])
            env_content = open(env_file).read()
            ucr = ConfigRegistry()
            ucr.load()
            assert ('TEST_HOSTNAME=%s' % ucr.get('hostname')) in env_content, env_content
            env_container = subprocess.check_output(['univention-app', 'shell', name, 'env'], text=True)
            assert ('TEST_HOSTNAME=%s' % ucr.get('hostname')) in env_container, env_container
        finally:
            app.uninstall()
            app.remove()
