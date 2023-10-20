#!/usr/share/ucs-test/runner python3
## desc: Check the App installation if the next free port is already used
## tags: [docker]
## exposure: dangerous
## packages:
##   - univention-docker

import subprocess

import apt

from univention.config_registry import handler_set
from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.utils import fail

from dockertest import (
    docker_image_is_present, docker_login, pull_docker_image, remove_docker_image, restart_docker, tiny_app,
)


def deb_package_is_installed(pkgname):
    cache = apt.Cache()
    return bool(cache[pkgname].is_installed)


def deb_install_package(pkgname):
    cmd = ['univention-install', '-y', pkgname]
    p = subprocess.Popen(cmd, close_fds=True)
    p.wait()


def deb_uninstall_package(pkgname):
    cmd = ['apt-get', 'purge', '-y', pkgname]
    p = subprocess.Popen(cmd, close_fds=True)
    p.wait()

    cmd = ['apt-get', 'autoremove', '-y']
    p = subprocess.Popen(cmd, close_fds=True)
    p.wait()


class TestCase:

    def __init__(self):
        self.ucr = UCSTestConfigRegistry()
        self.ucr.load()

        self.imgname = tiny_app().ini['DockerImage']

        required_pkgname = 'univention-squid'
        if not deb_package_is_installed(required_pkgname):
            deb_install_package(required_pkgname)
            self.remove_pkgname = required_pkgname
        else:
            self.remove_pkgname = None

        if not self.ucr.get('proxy/http'):
            handler_set(['proxy/http=http://127.0.0.1:3128/'])
            restart_docker()
            self.ucr_changed = True
        else:
            self.ucr_changed = False

    def run(self):
        if docker_image_is_present(self.imgname):
            remove_docker_image(self.imgname)

        docker_login()
        pull_docker_image(self.imgname)
        if not docker_image_is_present(self.imgname):
            fail('The container could not be downloaded.')

    def cleanup(self):
        remove_docker_image(self.imgname)
        if self.ucr_changed:
            self.ucr.revert_to_original_registry()
            restart_docker()
        if self.remove_pkgname:
            deb_uninstall_package(self.remove_pkgname)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            print(f'Cleanup after exception: {exc_type} {exc_value}')
        self.cleanup()


if __name__ == '__main__':

    with TestCase() as tc:
        tc.run()
