#!/usr/share/ucs-test/runner python3
## desc: Download metadata.php
## tags: [saml]
## exposure: safe

from urllib.request import urlopen

from univention.config_registry import ConfigRegistry
from univention.testing.utils import fail


if __name__ == '__main__':
    ucr = ConfigRegistry()
    ucr.load()

    metadata_url = ucr['umc/saml/idp-server']
    if metadata_url is None:
        fail('The ucr key umc/saml/idp-server is not set')

    res = []

    # read at least five times because ucs-sso is an alias for different IPs
    for i in range(0, 5):
        print('%d: Query metadata for %r' % (i, metadata_url))
        response = urlopen(metadata_url)  # noqa: S310
        metadata = response.read()
        if not metadata:
            fail('Empty response')
        print(metadata.decode('UTF-8', 'replace'))
        res.append(metadata)

    for i in range(0, 4):
        if res[i] != res[i + 1]:
            fail('Metadata is different: %d and %d' % (i, i + 1))
