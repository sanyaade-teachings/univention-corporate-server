# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the DHCP subnet
#
# Copyright 2004-2024 Univention GmbH
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

import ipaddr

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.ipaddress
import univention.admin.localization

from .__common import DHCPBase, add_dhcp_options, rangeUnmap, rangeMap

translation = univention.admin.localization.translation('univention.admin.handlers.dhcp')
_ = translation.translate

module = 'dhcp/subnet'
operations = ['add', 'edit', 'remove', 'search']
superordinate = 'dhcp/service'
childs = True
childmodules = ['dhcp/pool']
short_description = _('DHCP: Subnet')
object_name = _('DHCP subnet')
object_name_plural = _('DHCP subnets')
long_description = _('The IP address range used in a dedicated (non-shared) physical network.')
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionDhcpSubnet'],
	),
}
property_descriptions = {
	'subnet': univention.admin.property(
		short_description=_('Subnet address'),
		long_description=_('The network address.'),
		syntax=univention.admin.syntax.ipv4Address,
		include_in_default_search=True,
		required=True,
		may_change=False,
		identifies=True
	),
	'subnetmask': univention.admin.property(
		short_description=_('Address prefix length (or Netmask)'),
		long_description=_('The number of leading bits of the IP address used to identify the network.'),
		syntax=univention.admin.syntax.v4netmask,
		required=True,
	),
	'broadcastaddress': univention.admin.property(
		short_description=_('Broadcast address'),
		long_description=_('The IP addresses used to send data to all hosts inside the network.'),
		syntax=univention.admin.syntax.ipv4Address,
	),
	'range': univention.admin.property(
		short_description=_('Dynamic address assignment'),
		long_description=_('Define a pool of addresses available for dynamic address assignment.'),
		syntax=univention.admin.syntax.IPv4_AddressRange,
		multivalue=True,
	),
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('General DHCP subnet settings'), layout=[
			['subnet', 'subnetmask'],
			'broadcastaddress',
			'range'
		]),
	]),
]


mapping = univention.admin.mapping.mapping()
mapping.register('subnet', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('subnetmask', 'dhcpNetMask', None, univention.admin.mapping.ListToString)
mapping.register('broadcastaddress', 'univentionDhcpBroadcastAddress', None, univention.admin.mapping.ListToString)
mapping.register('range', 'dhcpRange', rangeMap, rangeUnmap)
add_dhcp_options(__name__)


class object(DHCPBase):
	module = module

	def ready(self):
		super(object, self).ready()

		if ipaddr.IPv4Network('%(subnet)s/%(subnetmask)s' % self.info).network != ipaddr.IPv4Address('%(subnet)s' % self.info):
			raise univention.admin.uexceptions.valueError(_('The subnet mask does not match the subnet.'), property='subnetmask')

		subnet = ipaddr.IPNetwork('%(subnet)s/%(subnetmask)s' % self.info)
		if self.hasChanged('range') or not self.exists():
			# TODO: replace univention.admin.ipaddress.*() with ipaddr module
			for addresses in self['range']:
				for addresses2 in self['range']:
					if addresses != addresses2 and univention.admin.ipaddress.is_range_overlapping(addresses, addresses2):
						raise univention.admin.uexceptions.rangesOverlapping('%s-%s; %s-%s' % (addresses[0], addresses[1], addresses2[0], addresses2[1]))

				for addr in addresses:
					if univention.admin.ipaddress.ip_is_network_address(self['subnet'], self['subnetmask'], addr):
						raise univention.admin.uexceptions.rangeInNetworkAddress('%s-%s' % (addresses[0], addresses[1]))

					if univention.admin.ipaddress.ip_is_broadcast_address(self['subnet'], self['subnetmask'], addr):
						raise univention.admin.uexceptions.rangeInBroadcastAddress('%s-%s' % (addresses[0], addresses[1]))

					if ipaddr.IPAddress(addr) not in subnet:
						raise univention.admin.uexceptions.rangeNotInNetwork(addr)

	@staticmethod
	def unmapped_lookup_filter():
		return univention.admin.filter.conjunction('&', [
			univention.admin.filter.expression('objectClass', 'univentionDhcpSubnet'),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'univentionDhcpSharedSubnet')])
		])


def identify(dn, attr):
	return 'univentionDhcpSubnet' in attr.get('objectClass', []) and 'univentionDhcpSharedSubnet' not in attr.get('objectClass', [])


lookup_filter = object.lookup_filter
lookup = object.lookup
