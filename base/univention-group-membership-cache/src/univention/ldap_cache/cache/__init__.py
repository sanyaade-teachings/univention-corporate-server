#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2021 Univention GmbH
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

from univention.ldap_cache.log import debug
from univention.ldap_cache.cache.plugins import Plugins
from univention.ldap_cache.cache.backend.gdbm_cache import GdbmCaches as Caches, GdbmCache as Cache, GdbmShard as Shard
#from univention.ldap_cache.cache.backend.lmdb_cache import LmdbCaches as Caches, LmdbCache as Cache, LmdbShard as Shard


class LowerValuesShard(Shard):
	def get_values(self, obj):
		values = super(LowerValuesShard, self).get_values(obj)
		return [value.lower() for value in values]


def get_cache():
	if get_cache._cache is None:
		debug('Creating the Caches instance')
		caches = Caches()
		for plugin in Plugins('univention.ldap_cache.cache.plugins'):
			caches.add(plugin)
		get_cache._cache = caches
	return get_cache._cache


get_cache._cache = None


def dn_to_entry_uuid(dn):
	cache = get_cache().get_sub_cache('EntryUUID')
	dn = dn.lower()
	for key, value in cache:
		if value == dn:
			return key


def entry_uuid_to_dn(entry_uuid):
	cache = get_cache().get_sub_cache('EntryUUID')
	return cache.get(entry_uuid)
