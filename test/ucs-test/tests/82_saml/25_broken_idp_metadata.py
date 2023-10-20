#!/usr/share/ucs-test/runner python3
## desc: Check that the umc server does not stop if the idp metadata is not available.
## tags: [saml]
## bugs: [39355]
## join: true
## exposure: dangerous

import os
import subprocess
import time

from univention.testing import utils

import samltest


def restart_umc():
    subprocess.check_call(["deb-systemd-invoke", "restart", "univention-management-console-server"])
    time.sleep(3)  # Wait for the umc to be ready to answer requests.


class move_idp_metadata:

    metadata_dir = "/usr/share/univention-management-console/saml/idp/"

    def __enter__(self):
        for metadata_file in os.listdir(self.metadata_dir):
            metadata_file_fullpath = self.metadata_dir + metadata_file
            os.rename(metadata_file_fullpath, metadata_file_fullpath + '.backup')
        restart_umc()

    def __exit__(self, exc_type, exc_value, traceback):
        for metadata_file in os.listdir(self.metadata_dir):
            metadata_file_fullpath = self.metadata_dir + metadata_file
            os.rename(metadata_file_fullpath, metadata_file_fullpath.replace('.backup', ''))
        restart_umc()


def main():
    account = utils.UCSTestDomainAdminCredentials()
    SamlSession = samltest.SamlTest(account.username, account.bindpw)
    with move_idp_metadata():
        try:
            SamlSession.login_with_new_session_at_IdP()
        except samltest.SamlError as exc:
            expected_error = "There is a configuration error in the service provider: No identity provider are set up for use."
            if expected_error not in str(exc):
                raise Exception({'expected': expected_error, 'got': str(exc)})
    SamlSession.logout_at_IdP()
    SamlSession.login_with_new_session_at_IdP()
    SamlSession.test_logged_in_status()
    SamlSession.logout_at_IdP()
    SamlSession.test_logout_at_IdP()
    SamlSession.test_logout()


if __name__ == '__main__':
    try:
        main()
    finally:
        # Make sure everything is in a working state again
        restart_umc()
    print("####Success: UMC server does not stop if the idp metadata is not available.####")
