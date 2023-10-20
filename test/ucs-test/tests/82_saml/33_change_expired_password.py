#!/usr/share/ucs-test/runner python3
## desc: Check whether it is possible to change expired password
## tags: [saml, skip_admember]
## join: true
## exposure: dangerous

import time

import pytest

import univention.config_registry
import univention.testing.udm as udm_test
from univention.testing import ucs_samba

import samltest


def main():
    ucr = univention.config_registry.ConfigRegistry()
    ucr.load()
    with udm_test.UCSTestUDM() as udm:
        testcase_user_name = udm.create_user(pwdChangeNextLogin='1')[1]
        if ucr.get('server/role') == 'memberserver' and ucs_samba.get_available_s4connector_dc():
            #  Make sure the user has been replicated or the password change can fail
            print('Wait for s4 replication')
            time.sleep(17)
        SamlSession = samltest.SamlTest(testcase_user_name, 'univention',)

        with pytest.raises(samltest.SamlPasswordExpired):
            SamlSession.login_with_new_session_at_IdP()

        # changing to the current password should fail
        with pytest.raises(samltest.SamlPasswordChangeFailed):
            SamlSession.change_expired_password('univention')

        SamlSession.change_expired_password('Univention.99')
        SamlSession.test_logged_in_status()


if __name__ == '__main__':
    main()
    print("Success: Login with pwdChangeNextLogin='1' set is not possible")
