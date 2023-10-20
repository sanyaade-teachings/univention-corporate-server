#!/usr/share/ucs-test/runner python3
## desc: Import 30.000 users and test the performance
## tags: [import30000,performance]
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
    MAX_SECONDS_IMPORT = 22 * 3600
    MAX_SECONDS_SAMBA_IMPORT = 128 * 3600 + CONNECTOR_WAIT_TIME
    MAX_SECONDS_ADMIN_AUTH = 8
    MAX_SECONDS_ADMIN_AUTH_UDM_LOAD = 13
    MAX_SECONDS_USER_CREATION = 135 + CONNECTOR_WAIT_TIME
    MAX_SECONDS_USER_AUTH = 20
    MAX_SECONDS_PASSWORD_RESET = 335 + CONNECTOR_WAIT_TIME

    CSV_IMPORT_FILE = '30000.csv'

    returnCode = 100

    create_ous([str(x) for x in range(10, 70,)])

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

    if not count_users(needed=30000):
        returnCode = 1

    sys.exit(returnCode)

# vim: set filetype=py
