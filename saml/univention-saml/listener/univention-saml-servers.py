# -*- coding: utf-8 -*-
#
# Univention SAML
# Listener module to set up SAML configuration
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2015-2024 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

from __future__ import annotations

import os.path
import subprocess
from typing import Dict, List

from univention.config_registry import ConfigRegistry, handler_set, handler_unset

import listener


description = 'Manage ucs/server/saml-idp-server/* variables'
filter = '(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))'
attributes = ['univentionService']


def handler(dn: str, new: Dict[str, List[bytes]], old: Dict[str, List[bytes]]) -> None:
    ucr = ConfigRegistry()
    ucr.load()
    listener.setuid(0)
    try:
        try:
            fqdn = '%s.%s' % (new['cn'][0].decode('UTF-8'), new['associatedDomain'][0].decode('ASCII'))
        except (KeyError, IndexError):
            return

        change = False
        if b'univention-saml' in new.get('univentionService', []):
            handler_set(['ucs/server/saml-idp-server/%s=%s' % (fqdn, fqdn)])
            change = True
        elif b'univention-saml' in old.get('univentionService', []):
            handler_unset(['ucs/server/saml-idp-server/%s' % (fqdn,)])
            change = True

        if change:
            path_to_cert = ucr.get('saml/idp/certificate/certificate')
            path_to_key = ucr.get('saml/idp/certificate/privatekey')
            if path_to_cert and os.path.exists(path_to_cert) and path_to_key and os.path.exists(path_to_key):
                subprocess.call(['systemctl', 'restart', 'univention-saml'])
    finally:
        listener.unsetuid()
