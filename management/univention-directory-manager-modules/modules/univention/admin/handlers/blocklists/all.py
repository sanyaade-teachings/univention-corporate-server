# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2024 Univention GmbH
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

"""|UDM| module for all |blocklist| objects"""


import univention.admin.blocklist
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
from univention.admin.layout import Tab


translation = univention.admin.localization.translation('univention.admin.handlers.blocklists')
_ = translation.translate


module = 'blocklists/all'

childs = False
short_description = _('All blocklist objects')
object_name = _('Blocklist')
object_name_plural = _('Blocklists')
long_description = _('Manage the blocklists')
operations = ['search']
childmodules = ['blocklists/list']
virtual = True
options = {}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description='',
        syntax=univention.admin.syntax.dnsName,
        include_in_default_search=True,
        required=True,
        identifies=True,
    ),
}
layout = [Tab(_('General'), _('Basic settings'), layout=["name"])]
mapping = univention.admin.mapping.mapping()


class object(univention.admin.handlers.simpleLdap):
    module = module
    ldap_base = univention.admin.blocklist.BLOCKLIST_BASE


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):
    ret = []
    blocklistentry_filter = None
    blocklist_filter = None
    if superordinate:
        ret += univention.admin.handlers.blocklists.entry.lookup(co, lo, blocklistentry_filter, base, superordinate, scope, unique, required, timeout, sizelimit)
    else:
        base = univention.admin.blocklist.BLOCKLIST_BASE
        ret += univention.admin.handlers.blocklists.list.lookup(co, lo, blocklist_filter, base, superordinate, scope, unique, required, timeout, sizelimit)
    return ret


def identify(dn, attr, canonical=False):
    pass
