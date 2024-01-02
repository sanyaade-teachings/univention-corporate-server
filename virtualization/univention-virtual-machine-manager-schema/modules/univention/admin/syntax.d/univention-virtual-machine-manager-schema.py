# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager
#  UDM Virtual Machine Manager syntax classes
#
# Copyright 2013-2024 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

import re

from univention.admin.syntax import UDM_Objects, simple
from univention.admin.localization import translation

_ = translation('univention.admin.handlers.uvmm').translate


class UvmmProfiles(UDM_Objects):
	description = _('UVMM: Profile')
	udm_modules = ('uvmm/profile',)
	label = '%(name)s (%(virttech)s)'
	empty_value = True
	use_objects = False


class UvmmCapacity(simple):
	min_length = 1
	max_length = 0
	regex = re.compile(r'^([0-9]+(?:[,.][0-9]+)?)[ \t]*(?:([KkMmGgTtPp])(?:[Ii]?[Bb])?|[Bb])?$')
	error_message = _("Value must be an positive capacity (xx.x [kmgtp][[i]B])")


class UvmmCloudType(UDM_Objects):
	description = _('UVMM: Cloud Types')
	udm_modules = ('uvmm/cloudtype',)
	label = '%(name)s'
	use_objects = False
