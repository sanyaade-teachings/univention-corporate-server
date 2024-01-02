#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Updater
#  Dump key id from license to local UCR variable
#
# Copyright 2013-2024 Univention GmbH
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

from __future__ import absolute_import

import listener
import univention.config_registry

name = 'license_uuid'
description = 'Dump key id from license to local UCR variable'
filter = '(&(objectClass=univentionLicense)(cn=admin))'


def handler(dn, new, old):
    if new:
        listener.setuid(0)
        try:
            ucrVars = ['license/base=%s' % new.get('univentionLicenseBaseDN')[0]]
            if new.get('univentionLicenseKeyID'):
                ucrVars.append('uuid/license=%s' % new.get('univentionLicenseKeyID')[0])
            else:
                univention.config_registry.handler_unset(['uuid/license'])
            univention.config_registry.handler_set(ucrVars)
        finally:
            listener.unsetuid()
