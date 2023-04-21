#!/usr/share/ucs-test/runner python3
## desc: Pull appbox docker image
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

from dockertest import docker_login, docker_pull


if __name__ == '__main__':
    docker_login()
    docker_pull('ucs-appbox-amd64:4.1-0')
