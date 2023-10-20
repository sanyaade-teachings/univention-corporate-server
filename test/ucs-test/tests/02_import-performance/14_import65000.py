#!/usr/share/ucs-test/runner python3
## desc: Import 65.000 users and test the performance
## tags: [import65000,performance]
## rolest: [domaincontroller_master]
## exposure: dangerous
## timeout: 0
## packages:
##   - ucs-school-import
##   - univention-s4-connector
##   - univention-samba4

import sys

from performanceutils import (
    CONNECTOR_WAIT_TIME, count_users, create_ous, create_test_user, execute_timing, get_user_dn_list, import_users,
    reset_passwords, s4_user_auth, test_umc_admin_auth, test_umc_admin_auth_udm_load, wait_for_s4connector,
)


if __name__ == '__main__':
    MAX_SECONDS_IMPORT = 16 * 3600
    MAX_SECONDS_SAMBA_IMPORT = 31 * 3600 + CONNECTOR_WAIT_TIME
    MAX_SECONDS_ADMIN_AUTH = 8
    MAX_SECONDS_ADMIN_AUTH_UDM_LOAD = 13
    MAX_SECONDS_USER_CREATION = 110 + CONNECTOR_WAIT_TIME
    MAX_SECONDS_USER_AUTH = 2
    MAX_SECONDS_PASSWORD_RESET = 120 + CONNECTOR_WAIT_TIME

    CSV_IMPORT_FILE = '65000.csv'

    returnCode = 100

    create_ous([str(x) for x in range(100, 230,)])

    if not execute_timing('user import', MAX_SECONDS_IMPORT, import_users, CSV_IMPORT_FILE,):
        returnCode = 1

    if not execute_timing('user import sync to s4', MAX_SECONDS_SAMBA_IMPORT, wait_for_s4connector,):
        returnCode = 1

    if not execute_timing('UMC authentication', MAX_SECONDS_ADMIN_AUTH, test_umc_admin_auth,):
        returnCode = 1

    if not execute_timing('UMC authentication UDM load', MAX_SECONDS_ADMIN_AUTH_UDM_LOAD, test_umc_admin_auth_udm_load,):
        returnCode = 1

    if not execute_timing('create test user', MAX_SECONDS_USER_CREATION, create_test_user,):
        returnCode = 1

    if not execute_timing('samba4 auth', MAX_SECONDS_USER_AUTH, s4_user_auth, 'Administrator', 'univention',):
        returnCode = 1

    user_dns = get_user_dn_list(CSV_IMPORT_FILE)

    if not execute_timing('user password reset', MAX_SECONDS_PASSWORD_RESET, reset_passwords, user_dns,):
        returnCode = 1

    if not count_users(needed=65000):
        returnCode = 1

    sys.exit(returnCode)

# vim: set filetype=py
