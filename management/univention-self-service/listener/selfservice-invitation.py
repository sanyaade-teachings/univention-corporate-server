#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention LDAP
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2019-2023 Univention GmbH
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

from __future__ import absolute_import, annotations

import os
from typing import Dict, List

import univention.debug as ud

import listener


# pwdChangeNextLogin=1 should be set, this is either shadowMax=1 or shadowLastChange=0
name = 'selfservice-invitation'
description = 'trigger selfservice email for new users with PasswordRecoveryEmail'
filter = '(&(univentionPasswordSelfServiceEmail=*)(uid=*)(|(shadowMax=1)(shadowLastChange=0)))'
modrdn = '1'
cache_dir = '/var/cache/univention-directory-listener/selfservice-invitation'


def handler(dn: str, new: Dict[str, List[bytes]], old: Dict[str, List[bytes]], command: str) -> None:
    if not listener.configRegistry.is_true('umc/self-service/invitation/enabled', True):
        return

    if listener.configRegistry.get('server/role', 'undefined') != 'domaincontroller_master':
        return

    if new and not old and command == 'a':
        filename = os.path.join(cache_dir, new.get('uid')[0].decode('UTF-8').replace('/', '') + '.send')
        ud.debug(ud.LISTENER, ud.PROCESS, '%s: trigger selfservice invitation for %r' % (name, dn))
        try:
            os.mknod(filename)
        except OSError as exc:
            if hasattr(exc, 'errno') and exc.errno == 17:
                pass
            else:
                raise
