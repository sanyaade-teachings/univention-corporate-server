#!/usr/share/ucs-test/runner python3
## desc: Check if SNI can be configured for dovecot with one additional host/cert
## exposure: dangerous
## roles: [domaincontroller_master, domaincontroller_backup]
## packages: [univention-mail-dovecot]
## bugs: [48485]
import socket
import ssl
import subprocess

import univention.config_registry
import univention.testing.ucr as ucr_test
from univention.testing import utils


def get_certificate_from_ssl_connection(fqdn, servername, port):
    context = ssl.create_default_context()
    context.check_hostname = False
    conn = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=servername)
    conn.connect((fqdn, port))
    return conn.getpeercert()


def check_if_correct_cert_is_served(fqdn, servername, port, must_fail=False):
    cert = get_certificate_from_ssl_connection(fqdn, servername, port)
    if not cert:
        utils.fail('Empty certificate from %s:%s with servername %s' % (fqdn, port, servername))

    try:
        ssl.match_hostname(cert, servername)
    except ssl.CertificateError as e:
        if must_fail:
            print('\nOK: Server was not configurd to deliver certificate for %s, the ssl.match_hostname() failed as expected\n' % (servername))
        else:
            utils.fail('Incorrect certificate returned: Requested certificate from %s:%s for servername %s, error: %s' % (fqdn, port, servername, e))


if __name__ == '__main__':
    # setup SNI certificate with another certificate
    with ucr_test.UCSTestConfigRegistry() as ucr:
        hostname = ucr.get('hostname')
        domain = ucr.get('domainname')
        fqdn = "%s.%s" % (hostname, domain)

        check_if_correct_cert_is_served(fqdn, 'ucs-sso.%s' % domain, 993, must_fail=True)

        univention.config_registry.handler_set([
            'mail/dovecot/ssl/sni/ucs-sso.%(domain)s/certificate=/etc/univention/ssl/ucs-sso.%(domain)s/cert.pem' % {'domain': domain},
            'mail/dovecot/ssl/sni/ucs-sso.%(domain)s/key=/etc/univention/ssl/ucs-sso.%(domain)s/private.key' % {'domain': domain},
        ])
        subprocess.call(['service', 'dovecot', 'restart'])

        print('\nTest if host %s returns a certificate for %s' % (fqdn, fqdn))
        utils.retry_on_error((lambda: check_if_correct_cert_is_served(fqdn, fqdn, 993)), exceptions=(Exception, ), retry_count=5)
        check_if_correct_cert_is_served(fqdn, fqdn, 995)
        print('Test if host %s returns a certificate for ucs-sso.%s' % (fqdn, domain))
        check_if_correct_cert_is_served(fqdn, 'ucs-sso.%s' % domain, 993)
        check_if_correct_cert_is_served(fqdn, 'ucs-sso.%s' % domain, 995)

        ucr.revert_to_original_registry()
        subprocess.call(['service', 'dovecot', 'restart'])
