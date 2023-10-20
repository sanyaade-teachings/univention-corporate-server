#!/usr/share/ucs-test/runner python3
## desc: Import 10.000 users in 20 schools with the new import script and test the performance
## tags: [newimport10000,performance]
## rolest: [domaincontroller_master]
## exposure: dangerous
## timeout: 0
## packages:
##   - ucs-school-import
##   - univention-s4-connector
##   - univention-samba4
## bugs: [43936]

import sys

from performanceutils import (
    CONNECTOR_WAIT_TIME, count_users, create_ous, create_test_user, execute_timing, get_user_dn_list_new,
    import_users_new, remove_ous, reset_passwords, s4_user_auth, test_umc_admin_auth, test_umc_admin_auth_udm_load,
    wait_for_s4connector,
)

import univention.testing.strings as uts


if __name__ == '__main__':

    MAX_SECONDS_OU_CREATION = 30 * 60
    MAX_SECONDS_IMPORT = 4 * 3600
    MAX_SECONDS_SAMBA_IMPORT = 4 * 3600 + CONNECTOR_WAIT_TIME
    MAX_SECONDS_ADMIN_AUTH_UDM_LOAD = 13
    MAX_SECONDS_ADMIN_AUTH = 8
    MAX_SECONDS_USER_CREATION = 135 + CONNECTOR_WAIT_TIME
    MAX_SECONDS_USER_AUTH = 20
    MAX_SECONDS_PASSWORD_RESET = 335 + CONNECTOR_WAIT_TIME

    test_user_kwargs = {
        "CSV_IMPORT_FILE": '/tmp/import10000.csv',
        "ous": 20,
        "teachers": 800,
        "staff": 500,
        "staffteachers": 200,
        "students": 8500,
        "classes": 400,
    }
    school_names = [f'School{num:0>2}{uts.random_name(5)}' for num in range(test_user_kwargs['ous'])]
    cmd_args = '-v --teachers {teachers} --staff {staff} --staffteachers {staffteachers} --students {students} --classes {classes} --csvfile {CSV_IMPORT_FILE} {school_names}'.format(school_names=' '.join(school_names), **test_user_kwargs,)

    returnCode = 100

    if not execute_timing('create OUs', MAX_SECONDS_OU_CREATION, create_ous, school_names,):
        returnCode = 1

    if not execute_timing('new user import', MAX_SECONDS_IMPORT, import_users_new, cmd_args,):
        returnCode = 1

    if not execute_timing('new user import sync to s4', MAX_SECONDS_SAMBA_IMPORT, wait_for_s4connector,):
        returnCode = 1

    if not execute_timing('UMC authentication', MAX_SECONDS_ADMIN_AUTH, test_umc_admin_auth,):
        returnCode = 1

    if not execute_timing('UMC authentication UDM load', MAX_SECONDS_ADMIN_AUTH_UDM_LOAD, test_umc_admin_auth_udm_load,):
        returnCode = 1

    if not execute_timing('create test user', MAX_SECONDS_USER_CREATION, create_test_user,):
        returnCode = 1

    if not execute_timing('samba4 auth', MAX_SECONDS_USER_AUTH, s4_user_auth, 'Administrator', 'univention',):
        returnCode = 1

    user_dns = get_user_dn_list_new(test_user_kwargs['CSV_IMPORT_FILE'])

    if not execute_timing('user password reset', MAX_SECONDS_PASSWORD_RESET, reset_passwords, user_dns,):
        returnCode = 1

    if not count_users(needed=test_user_kwargs['teachers'] + test_user_kwargs['staff'] + test_user_kwargs['staffteachers'] + test_user_kwargs['students']):
        returnCode = 1

    if not execute_timing('remove OUs', MAX_SECONDS_OU_CREATION, remove_ous, school_names,):
        returnCode = 1

    sys.exit(returnCode)

# vim: set filetype=py
