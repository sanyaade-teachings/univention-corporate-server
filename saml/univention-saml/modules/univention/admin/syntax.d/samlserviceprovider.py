# -*- coding: utf-8 -*-
#
# Univention Management Console
#  samlserviceprovider: syntax file
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

import univention.admin.modules
import univention.admin.syntax


class samlserviceprovider(univention.admin.syntax.UDM_Objects):
	udm_modules = ('saml/serviceprovider', )
	regex = None


class attributeMapping(univention.admin.syntax.complex):
	"""
	Syntax for key-value-pairs separated by `=` where the value is optional.

	"""
	delimiter = ' = '
	subsyntaxes = [(_('LDAP Attribute Name'), univention.admin.syntax.string), (_('Service Attribute Name'), univention.admin.syntax.string)]
	subsyntax_key_value = True
	all_required = 0
	min_elements = 1

