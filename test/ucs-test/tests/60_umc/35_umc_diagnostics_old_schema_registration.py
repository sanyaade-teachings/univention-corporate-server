#!/usr/share/ucs-test/runner python3
## desc: Test basic schema registration
## tags:
##  - ldapextensions
##  - apptest
## roles:
##  - domaincontroller_master
## roles-not:
##  - basesystem
## packages:
##  - python3-univention-lib
## exposure: dangerous

import os
import subprocess
import traceback

import ldap
from retrying import retry

from univention.config_registry import ucr
from univention.management.console.modules import diagnostic
from univention.testing.strings import random_int
from univention.testing.utils import fail


attribute_id = random_int() + random_int() + random_int() + random_int() + random_int()
schema_name = 'univention-corporate-client.schema'
filename = os.path.join('/tmp/', schema_name)
diagnostic_plugin = '60_old_schema_registration'

schema_buffer = '''
attributetype ( 1.3.6.1.4.1.10176.200.10999.%(attribute_id)s NAME 'univentionFreeAttribute%(attribute_id)s'
    DESC ' unused custom attribute %(attribute_id)s '
    EQUALITY caseExactMatch
    SUBSTR caseIgnoreSubstringsMatch
    SYNTAX 1.3.6.1.4.1.1466.115.121.1.15 )
''' % {'attribute_id': attribute_id}


def write_schema_file(filename, schema_buffer):
    with open(filename, 'w+') as fd:
        fd.write(schema_buffer)


def ucs_register_ldap_schema(filename):
    subprocess.check_call(['bash', '-c', 'source /usr/share/univention-lib/ldap.sh; ucs_registerLDAPSchema %s' % filename])


def ucs_unregister_ldap_extension(schema_name):
    subprocess.check_call(['bash', '-c', 'source /usr/share/univention-lib/ldap.sh; ucs_unregisterLDAPExtension --schema %s' % schema_name[:-7]])


@retry(retry_on_exception=ldap.SERVER_DOWN, stop_max_attempt_number=ucr.get_int('ldap/client/retry/count', 15) + 1)
def __fetch_schema_from_uri(ldap_uri):
    return ldap.schema.subentry.urlfetch(ldap_uri)


def fetch_schema_from_ldap_master():
    ldap_uri = 'ldap://%(ldap/master)s:%(ldap/master/port)s' % ucr
    return __fetch_schema_from_uri(ldap_uri)


def test():
    try:
        write_schema_file(filename, schema_buffer)
        ucs_register_ldap_schema(filename)

        # start the diagnostic check
        old_schema_registration = diagnostic.Plugin(diagnostic_plugin)
        result = old_schema_registration.execute(None)
        assert not result['success'], 'old schema not detected'
        assert {'action': 'register_schema', 'label': 'Register Schema files'} in result['buttons'], 'repair button not shown'

        # repair button
        old_schema_registration.execute(None, action='register_schema')

        # check if schema is registered properly now
        schema = fetch_schema_from_ldap_master()
        attribute_identifier = "( 1.3.6.1.4.1.10176.200.10999.%(attribute_id)s NAME 'univentionFreeAttribute%(attribute_id)s" % {'attribute_id': attribute_id}

        for attribute_entry in schema[1].ldap_entry().get('attributeTypes'):
            if attribute_entry.startswith(attribute_identifier):
                print('The schema entry was found: %s' % attribute_entry)
                break
        else:
            fail('The attribute was not found: univentionFreeAttribute%(attribute_id)s' % {'attribute_id': attribute_id})
    finally:
        # cleanup
        try:
            ucs_unregister_ldap_extension(schema_name)
        except Exception:
            print('couldnt unregister')
            traceback.print_exc()
        try:
            os.remove(filename)
        except Exception:
            print('couldnt remove file')


test()

# vim: set ft=python :
