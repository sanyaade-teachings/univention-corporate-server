#!/usr/share/ucs-test/runner python3
## desc: Test if SAML user was created successfully
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## packages:
##  - univention-saml
## exposure: safe
## tags:
##  - skip_admember

from univention.config_registry import ConfigRegistry
from univention.testing import utils


if __name__ == '__main__':
    ucr = ConfigRegistry()
    ucr.load()
    attrs = {
        'uid': ['sys-idp-user'],
        'objectClass': ['top', 'person', 'univentionPWHistory', 'simpleSecurityObject', 'uidObject', 'univentionObject'],
        'univentionObjectType': ['users/ldap'],
    }
    utils.verify_ldap_object('uid=sys-idp-user,cn=users,%s' % (ucr['ldap/base'],), attrs,)
