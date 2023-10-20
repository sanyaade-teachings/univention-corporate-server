#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: test univention-ldap-backup
## versions:
##  5.0-2: fixed
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: careful

import os
import subprocess
from datetime import datetime
from os.path import exists
from pathlib import Path
from stat import S_IMODE

import pytest

from univention.testing.strings import random_username


current_date = datetime.now().strftime("%Y%m%d")

ldap_backup_path = Path(f"/var/univention-backup/ldap-backup_{current_date}.ldif.gz")
ldap_backup_log_path = Path(f"/var/univention-backup/ldap-backup_{current_date}.log.gz")


@pytest.fixture()
def cleanup():
    """Remove backup files"""
    yield
    print("** Cleaning up")
    os.remove(ldap_backup_path)
    os.remove(ldap_backup_log_path)


def create_owner(udm):
    """Create user"""
    _, user_name = udm.create_user(
        wait_for_replication=True,
        check_for_drs_replication=True,
        wait_for=True)
    return user_name


def create_group(udm):
    """Create group"""
    _, group_name = udm.create_group(
        wait_for_replication=True,
        check_for_drs_replication=True,
        wait_for=True,
    )
    subprocess.check_call('/usr/lib/univention-pam/ldap-group-to-file.py')
    return group_name


def are_valid_permissions(permissions):
    """Check if permissions are valid"""
    return 0o100 <= permissions <= 0o7777


def create_backup():
    """Run the backup"""
    return subprocess.call(["/usr/sbin/univention-ldap-backup"])


def check_backup_exists():
    """Check the backup files exist"""
    print("** Checking that the backup exists")
    assert exists(ldap_backup_path)
    assert exists(ldap_backup_log_path)


def check_ldap_backup_owner(owner="root"):
    """Check backup file owner is the expected"""
    print(f"** Checking expected owner ({owner})")
    assert owner == ldap_backup_path.owner()
    assert owner == ldap_backup_log_path.owner()


def check_ldap_backup_group(group="root"):
    """Check backup file group is the expected"""
    print(f"** Checking expected group ({group})")
    assert group == ldap_backup_path.group()
    assert group == ldap_backup_log_path.group()


def check_ldap_backup_permissions(permissions=0o600):
    """Check backup file permissions are the expected"""
    print(f"** Checking expected permissions ({permissions})")
    for path in [ldap_backup_path, ldap_backup_log_path]:
        stat = os.stat(path)
        assert S_IMODE(stat.st_mode) == permissions


@pytest.mark.tags('slapd-backup', 'univention-ldap-backup')
def test_run_default_backup(udm, ucr, cleanup):
    """Test backup when custom variables were unset"""
    ucr.handler_unset([
        "slapd/backup/group",
        "slapd/backup/owner",
        "slapd/backup/permissions",
    ])
    # Expected default values
    group = "root"
    owner = "root"
    permissions = 0o600
    print(f"** Creating default backup with {owner}:{group} {permissions:04o}")
    exit_code = create_backup()
    check_backup_exists()
    check_ldap_backup_owner(owner)
    check_ldap_backup_group(group)
    check_ldap_backup_permissions(permissions)
    assert exit_code == 0


@pytest.mark.tags('slapd-backup', 'univention-ldap-backup')
@pytest.mark.parametrize("owner", [None, "root"])
@pytest.mark.parametrize("group", [None, "root"])
@pytest.mark.parametrize(
    "permissions",
    [
        0o400,
        0o600,
        0o640,
        0o440,
        0o7777 + 1,  # an invalid case
    ],
)
def test_run_custom_backup(owner, group, permissions, udm, ucr, cleanup):
    """Test backup when variables were all set and valid"""
    owner = create_owner(udm) if owner is None else owner
    group = create_group(udm) if group is None else group
    ucr.handler_set([
        "slapd/backup/group=%s" % (group),
        "slapd/backup/owner=%s" % (owner),
        f"slapd/backup/permissions={permissions:o}",
    ])
    print(f"** Creating custom backup with {owner}:{group} {permissions:04o}")
    exit_code = create_backup()
    check_backup_exists()
    if are_valid_permissions(permissions):
        check_ldap_backup_permissions(permissions)
        check_ldap_backup_owner(owner)
        check_ldap_backup_group(group)
    else:
        check_ldap_backup_permissions()
        check_ldap_backup_owner("root")
        check_ldap_backup_group("root")
    assert exit_code == 0


@pytest.mark.tags('slapd-backup', 'univention-ldap-backup')
@pytest.mark.parametrize(
    "owner, group",
    [
        ("root", random_username()),
        (random_username(), "root"),
    ],
)
@pytest.mark.parametrize(
    "permissions",
    [
        0o400,
        0o600,
        0o640,
        0o440,
    ],
)
def test_non_existing_owner_group(owner, group, permissions, udm, ucr, cleanup):
    """Test backup when variables were all set but non existing owner or group"""
    print("** Checking a non existing user or group cannot own a backup")
    ucr.handler_set([
        "slapd/backup/group=%s" % (group),
        "slapd/backup/owner=%s" % (owner),
        f"slapd/backup/permissions={permissions:o}",
    ])
    exit_code = create_backup()
    check_backup_exists()
    check_ldap_backup_owner("root")
    check_ldap_backup_group("root")
    check_ldap_backup_permissions(0o600)
    assert exit_code == 0
