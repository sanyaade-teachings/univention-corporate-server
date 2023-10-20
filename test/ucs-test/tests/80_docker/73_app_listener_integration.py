#!/usr/share/ucs-test/runner python3
## desc: Test appcenter listener/converter
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import glob
import json
import os
import subprocess
import time

import univention.testing.udm as udm_test

from dockertest import App, Appcenter


APP_NAME = 'my-listener-test-app'
DB_FILE = f'/var/lib/univention-appcenter/apps/{APP_NAME}/data/db.json'
LISTENER_DIR = f'/var/lib/univention-appcenter/apps/{APP_NAME}/data/listener/'
LISTENER_TIMEOUT = 10


def dump_db():
    with open(DB_FILE) as f:
        db = json.load(f)
    return db


def obj_exists(obj_type, dn):
    found = False
    db = dump_db()
    for _obj_id, obj in db[obj_type].items():
        if dn.lower() == obj.get('dn').lower():
            found = True
    return found


def user_exists(dn):
    return obj_exists('users/user', dn)


def group_exists(dn):
    return obj_exists('groups/group', dn)


def get_attr(obj_type, dn, attr):
    db = dump_db()
    for _obj_id, obj in db[obj_type].items():
        if dn.lower() == obj.get('dn').lower():
            return obj['obj'].get(attr)


def test_listener():
    with udm_test.UCSTestUDM() as udm:
        # create
        u1 = udm.create_user(username='litest1')
        u2 = udm.create_user(username='litest2')
        u3 = udm.create_user(username='litest3')
        g1 = udm.create_group(name='ligroup1')
        g2 = udm.create_group(name='ligroup2')
        time.sleep(LISTENER_TIMEOUT)
        assert user_exists(u1[0])
        assert user_exists(u2[0])
        assert user_exists(u3[0])
        assert group_exists(g1[0])
        assert group_exists(g2[0])
        # modify
        udm.modify_object('users/user', dn=u1[0], description='abcde')
        udm.modify_object('users/user', dn=u2[0], description='xyz')
        udm.modify_object('users/user', dn=u3[0], description='öäü????ßßßß!')
        udm.modify_object('groups/group', dn=g1[0], description='lkjalkhlÄÖ#üäööäö')
        udm.modify_object('groups/group', dn=g2[0], users=u1[0])
        time.sleep(LISTENER_TIMEOUT)
        assert get_attr('users/user', u1[0], 'description') == 'abcde'
        assert get_attr('users/user', u2[0], 'description') == 'xyz'
        assert get_attr('users/user', u3[0], 'description') == 'öäü????ßßßß!'
        assert get_attr('users/user', u1[0], 'description')
        assert get_attr('users/user', u1[0], 'disabled') is False
        assert get_attr('users/user', u1[0], 'displayName')
        assert get_attr('users/user', u1[0], 'gidNumber')
        assert get_attr('users/user', u1[0], 'groups')
        assert get_attr('users/user', u1[0], 'lastname')
        assert get_attr('users/user', u1[0], 'sambaRID')
        assert get_attr('groups/group', g1[0], 'description') == 'lkjalkhlÄÖ#üäööäö'
        assert get_attr('groups/group', g2[0], 'users') == [u1[0]]
        assert get_attr('groups/group', g2[0], 'users')
        assert get_attr('groups/group', g2[0], 'gidNumber')
        assert get_attr('groups/group', g2[0], 'name')
        assert get_attr('groups/group', g2[0], 'sambaRID')
        # remove
        udm.remove_object('users/user', dn=u1[0])
        udm.remove_object('users/user', dn=u2[0])
        udm.remove_object('users/user', dn=u3[0])
        udm.remove_object('groups/group', dn=g1[0])
        udm.remove_object('groups/group', dn=g2[0])
        time.sleep(LISTENER_TIMEOUT)
        assert not user_exists(u1[0])
        assert not user_exists(u2[0])
        assert not user_exists(u3[0])
        assert not group_exists(g1[0])
        assert not group_exists(g2[0])
        # listener dir should be empty at this point
        assert not glob.glob(os.path.join(LISTENER_DIR, '*.json'))


def get_pid_for_name(name):
    o = subprocess.check_output(['ps', 'aux'], text=True)
    for line in o.split('\n'):
        if name in line:
            return line.split()[1]
    return None


def systemd_service_active(service):
    active = False
    cmd = ['systemctl', 'status', service]
    try:
        out = subprocess.check_output(cmd, text=True)
    except subprocess.CalledProcessError:
        out = ''
    if 'Active: active (running' in out:
        active = True
    return active


def systemd_service_enabled(service):
    cmd = ['systemctl', 'is-enabled', service]
    try:
        out = subprocess.check_output(cmd, text=True)
    except subprocess.CalledProcessError:
        out = ''
    return 'enabled' in out


if __name__ == '__main__':

    name = APP_NAME
    systemd_service = f'univention-appcenter-listener-converter@{name}.service'

    setup = '''#!/bin/bash
export DEBIAN_FRONTEND=noninteractive
apt-get -y update
apt-get -y install python3
exit 0
'''
    store_data = '#!/bin/sh'
    preinst = f'''#!/bin/bash
ucr set appcenter/apps/{name}/docker/params=' -t'
exit 0
'''

    listener_trigger = f'''#!/usr/bin/python3

import glob
import os
import json

DATA_DIR = '/var/lib/univention-appcenter/apps/{name}/data/listener'
DB = '/var/lib/univention-appcenter/apps/{name}/data/db.json'

if not os.path.isfile(DB):
    with open(DB, 'w') as fd:
        json.dump({{'users/user': {{}}, 'groups/group': {{}}}}, fd, sort_keys=True, indent=4)

for i in sorted(glob.glob(os.path.join(DATA_DIR, '*.json'))):

    with open(DB) as fd:
        db = json.load(fd)

    with open(i) as fd:
        dumped = json.load(fd)
        action = 'add/modify'
        if dumped.get('object') is None:
            action = 'delete'

        if action == 'delete':
            if dumped.get('id') in db[dumped.get('udm_object_type')]:
                del db[dumped.get('udm_object_type')][dumped.get('id')]
        else:
            db[dumped.get('udm_object_type')][dumped.get('id')] = dict(
                id=dumped.get('id'),
                dn=dumped.get('dn'),
                obj=dumped.get('object'),
            )

    with open(DB, 'w') as fd:
        json.dump(db, fd, sort_keys=True, indent=4)

    os.remove(i)
'''

    with Appcenter() as appcenter:
        app = App(name=name, version='1', build_package=False, call_join_scripts=False)
        app.set_ini_parameter(
            DockerImage='docker-test.software-univention.de/debian:stable',
            DockerScriptSetup='/setup',
            DockerScriptStoreData='/store_data',
            DockerScriptInit='/bin/bash',
            ListenerUdmModules='users/user, groups/group',
        )
        app.add_script(setup=setup)
        app.add_script(store_data=store_data)
        app.add_script(preinst=preinst)
        app.add_script(listener_trigger=listener_trigger)
        app.add_to_local_appcenter()
        appcenter.update()
        app.install()
        appcenter.apps.append(app)
        app.verify(joined=False)
        images = subprocess.check_output(['docker', 'images'], text=True)
        assert 'stable' in images, images
        very_old_con_pid = get_pid_for_name('univention-appcenter-listener-converter %s' % name)
        time.sleep(10)
        with open('/var/lib/univention-directory-listener/handlers/%s' % name) as f:
            status = f.readline()
            assert status == '3'
        test_listener()

        # check listener/converter restart during update
        old_li_pid = get_pid_for_name(' /usr/sbin/univention-directory-listener')
        old_con_pid = get_pid_for_name('univention-appcenter-listener-converter %s' % name)
        assert very_old_con_pid == old_con_pid  # should be the same until now
        app = App(name=name, version='2', build_package=False, call_join_scripts=False)
        app.set_ini_parameter(
            DockerImage='docker-test.software-univention.de/debian:testing',
            DockerScriptSetup='/setup',
            DockerScriptStoreData='/store_data',
            DockerScriptInit='/bin/bash',
            ListenerUdmModules='users/user, groups/group',
        )
        app.add_script(setup=setup)
        app.add_script(store_data=store_data)
        app.add_script(preinst=preinst)
        app.add_script(listener_trigger=listener_trigger)
        app.add_to_local_appcenter()
        appcenter.update()
        app.upgrade()
        app.verify(joined=False)

        li_pid = get_pid_for_name(' /usr/sbin/univention-directory-listener')
        con_pid = get_pid_for_name('univention-appcenter-listener-converter %s' % name)
        assert old_li_pid == li_pid  # app update does not require listener restart
        assert old_con_pid != con_pid

        # check handler file/listener restart during remove
        app.uninstall()
        new_li_pid = get_pid_for_name(' /usr/sbin/univention-directory-listener')
        assert not systemd_service_enabled(systemd_service)
        assert not os.path.isfile('/var/lib/univention-directory-listener/handlers/%s' % name)
        assert li_pid != new_li_pid
