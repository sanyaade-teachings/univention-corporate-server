#!/usr/share/ucs-test/runner python3
## desc: Download certificate
## tags: [saml]
## roles: [domaincontroller_master, domaincontroller_backup]
## bugs: [44704]
## exposure: safe

import re
from urllib.request import urlopen

from univention.config_registry import ConfigRegistry
from univention.testing.utils import fail


def extract_base64_certificate_from_cert(certificate,):
    certificate = certificate.replace("\n", "",)
    base64_cert = re.search('.*-----BEGIN CERTIFICATE-----(?P<base64>.*)-----END CERTIFICATE-----.*', certificate,).group('base64')
    return base64_cert


def extract_base64_certificate_from_metadata(metadata,):
    metadata = metadata.replace("\n", "",)
    base64_cert = re.search('.*<ds:X509Certificate>(?P<base64>.*)</ds:X509Certificate>.*', metadata,).group('base64')
    return base64_cert


if __name__ == '__main__':
    ucr = ConfigRegistry()
    ucr.load()

    metadata_url = ucr['saml/idp/entityID']
    if metadata_url is None:
        fail('The ucr key saml/idp/entityID is not set')
    cert_url = metadata_url.replace('metadata.php', 'certificate',)

    res = []

    # read at least five times because ucs-sso is an alias for different IPs
    for i in range(0, 5,):
        print('%d: Query cert for %r' % (i, cert_url))
        response = urlopen(cert_url)  # noqa: S310
        cert = response.read().decode('ASCII')
        if not cert:
            fail('Empty response')
        print(cert)
        res.append(cert)

    for i in range(0, 4,):
        if res[i] != res[i + 1]:
            fail('Certificate is different: %d and %d' % (i, i + 1))

    print("Compare certificate with metadata")
    base64_cert = extract_base64_certificate_from_cert(cert)
    response = urlopen(metadata_url)  # noqa: S310
    metadata = response.read().decode('ASCII')
    if extract_base64_certificate_from_metadata(metadata) != base64_cert:
        fail('Certificate is different from the certificate in the metadata')
    print("Certificate OK")
