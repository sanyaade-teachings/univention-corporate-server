#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2017-2023 Univention GmbH
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
# you and Univention.
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

from typing import Dict, List, Optional

from univention.listener import ListenerModuleHandler


class ListenerModuleTemplate(ListenerModuleHandler):

    class Configuration(object):
        name = 'unique_name'
        description = 'listener module description'
        ldap_filter = '(&(objectClass=inetOrgPerson)(uid=example))'
        attributes = ['sn', 'givenName']

    def create(self, dn: str, new: Dict[str, List[bytes]],) -> None:
        self.logger.debug('dn: %r', dn,)

    def modify(
            self,
            dn: str,
            old: Dict[str, List[bytes]],
            new: Dict[str, List[bytes]],
            old_dn: Optional[str],) -> None:
        self.logger.debug('dn: %r', dn,)
        if old_dn:
            self.logger.debug('it is (also) a move! old_dn: %r', old_dn,)
        self.logger.debug('changed attributes: %r', self.diff(old, new,),)

    def remove(self, dn: str, old: Dict[str, List[bytes]],) -> None:
        self.logger.debug('dn: %r', dn,)
