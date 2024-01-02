#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2021-2024 Univention GmbH
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
#

from logging import getLogger

from univention.ldap_cache.cache import get_cache
from univention.listener.handler import ListenerModuleHandler


class LdapCacheHandler(ListenerModuleHandler):
	def __init__(self, *args, **kwargs):
		self._counter = 0
		super(LdapCacheHandler, self).__init__(*args, **kwargs)
		cache_logger = getLogger('univention.ldap_cache')
		cache_logger.setLevel(self.logger.level)
		for handler in self.logger.handlers:
			cache_logger.addHandler(handler)

	def _cleanup_cache_if_needed(self):
		self._counter += 1
		if self._counter % 1000 == 0:
			for name, db in get_cache():
				db.cleanup()

	def create(self, dn, new):
		self._cleanup_cache_if_needed()
		for shard in get_cache().get_shards_for_query(self._get_configuration().get_ldap_filter()):
			shard.add_object((dn, new))

	def modify(self, dn, old, new, old_dn):
		self._cleanup_cache_if_needed()
		for shard in get_cache().get_shards_for_query(self._get_configuration().get_ldap_filter()):
			shard.rm_object((old_dn or dn, old))
			shard.add_object((dn, new))

	def remove(self, dn, old):
		self._cleanup_cache_if_needed()
		for shard in get_cache().get_shards_for_query(self._get_configuration().get_ldap_filter()):
			shard.rm_object((dn, old))

	def post_run(self):
		self._counter = -1
		self._cleanup_cache_if_needed()

	class Configuration(ListenerModuleHandler.Configuration):
		def get_priority(self):
			return 2.0
