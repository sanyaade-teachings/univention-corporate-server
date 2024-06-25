#!/usr/share/ucs-test/runner pytest-3 -svvv
## desc: Test setting the quota through pam with usrjquota, the j is for journaled
## roles-not: [basesystem]
## exposure: dangerous
## packages:
##   - univention-quota

from quota_test import QuotaCheck


def test_usrjquota_pam() -> None:
    quotaCheck = QuotaCheck(quota_type="usrjquota=aquota.user,jqfmt=vfsv1")
    quotaCheck.test_quota_pam()
