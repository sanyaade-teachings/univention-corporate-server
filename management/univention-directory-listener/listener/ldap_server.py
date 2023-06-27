#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Directory Listener
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2023 Univention GmbH
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

"""listener script for setting ldap server."""

from __future__ import absolute_import, annotations

from typing import Dict, List

import univention.debug as ud
from univention.config_registry import handler_set, ucr_live as ucr

import listener


description = 'Update upstream LDAP server list'
filter = '(&(objectClass=univentionDomainController)(|(univentionServerRole=master)(univentionServerRole=backup)))'


def handler(dn: str, new: Dict[str, List[bytes]], old: Dict[str, List[bytes]]) -> None:
    """Handle change in LDAP."""
    if listener.configRegistry['server/role'] == 'domaincontroller_master':
        return

    listener.setuid(0)
    try:
        if 'univentionServerRole' in new:
            try:
                domain = new['associatedDomain'][0].decode('UTF-8')
            except LookupError:
                domain = ucr['domainname']
            add_ldap_server(new['cn'][0].decode('UTF-8'), domain, new['univentionServerRole'][0].decode('UTF-8'))
        elif 'univentionServerRole' in old and not new:
            try:
                domain = old['associatedDomain'][0].decode('UTF-8')
            except LookupError:
                domain = ucr['domainname']
            remove_ldap_server(old['cn'][0].decode('UTF-8'), domain, old['univentionServerRole'][0].decode('UTF-8'))
    finally:
        listener.unsetuid()


def add_ldap_server(name: str, domain: str, role: str) -> None:
    """Add LDAP server."""
    ud.debug(ud.LISTENER, ud.INFO, 'LDAP_SERVER: Add ldap_server %s' % name)

    server_name = "%s.%s" % (name, domain)

    if role == 'master':
        old_master = ucr.get('ldap/master')

        changes = ['ldap/master=%s' % server_name]

        if ucr.get('kerberos/adminserver') == old_master:
            changes.append('kerberos/adminserver=%s' % server_name)

        if ucr.get('ldap/server/name') == old_master:
            changes.append('ldap/server/name=%s' % server_name)

        handler_set(changes)

    if role == 'backup':
        backup_list = ucr.get('ldap/backup', '').split()
        if server_name not in backup_list:
            backup_list.append(server_name)
            handler_set(['ldap/backup=%s' % (' '.join(backup_list),)])


def remove_ldap_server(name: str, domain: str, role: str) -> None:
    """Remove LDAP server."""
    ud.debug(ud.LISTENER, ud.INFO, 'LDAP_SERVER: Remove ldap_server %s' % name)

    server_name = "%s.%s" % (name, domain)

    if role == 'backup':
        backup_list = ucr.get('ldap/backup', '').split()
        if server_name in backup_list:
            backup_list.remove(server_name)
            handler_set(['ldap/backup=%s' % (' '.join(backup_list),)])
