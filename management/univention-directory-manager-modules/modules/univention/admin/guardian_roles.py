# -*- coding: utf-8 -*-
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

"""|UDM| guardian roles handling"""

import re
from logging import getLogger

import univention.admin
import univention.admin.localization
import univention.admin.mapping
from univention.admin.layout import Tab
from univention.admin.syntax import simple


log = getLogger('ADMIN')

translation = univention.admin.localization.translation('univention.admin')
_ = translation.translate


# TODO move to univention.admin.syntax
class GuardianRole(simple):
    regex = re.compile(
        r"^([a-z0-9-_]+:[a-z0-9-_]+:[a-z0-9-_]+)(&[a-z0-9-_]+:[a-z0-9-_]+:[a-z0-9-_]+)?$"
    )
    error_message = _(
        "Guardian role strings must be lowercase ASCII alphanumeric with hyphens and underscores, "
        "in the format 'app:namespace:role' or 'app:namespace:role&app:namespace:context'!"
    )


def member_role_properties():
    return {
        'guardianMemberRoles': univention.admin.property(
            short_description=_('Roles used by Guardian for access permissions, these roles are passed to the members of this group'),
            long_description=_("Lowercase ASCII alphanumeric string with underscores or dashes, in the format 'app:namespace:role' or 'app:namespace:role&app:namespace:context'"),
            syntax=GuardianRole,
            multivalue=True,
        )
    }


def role_properties():
    return {
        'guardianRoles': univention.admin.property(
            short_description=_('Roles used by Guardian for access permissions'),
            long_description=_("Lowercase ASCII alphanumeric string with underscores or dashes, in the format 'app:namespace:role' or 'app:namespace:role&app:namespace:context'"),
            syntax=GuardianRole,
            multivalue=True,
        ),
        'guardianInheritedRoles': univention.admin.property(
            short_description=_('Roles used by Guardian for access permissions. Inherited by group membership'),
            long_description=_('Roles used by Guardian for access permissions. Inherited by group membership'),
            syntax=GuardianRole,
            may_change=False,
            multivalue=True,
            dontsearch=True,
            show_in_lists=False,
            cli_enabled=False,
        ),
    }


def register_member_role_mapping(mapping):
    mapping.register('guardianMemberRoles', 'univentionGuardianMemberRoles', None, None)


def register_role_mapping(mapping):
    mapping.register('guardianRoles', 'univentionGuardianRoles', None, None)


def member_role_layout():
    return Tab(
        _('Guardian'),
        _('Manage roles that are used for authorization'),
        advanced=True,
        layout=[
            'guardianMemberRoles',
        ],
    )


def role_layout():
    return Tab(
        _('Guardian'),
        _('Manage roles that are used for authorization'),
        advanced=True,
        layout=[
            'guardianRoles',
            'guardianInheritedRoles'
        ],
    )
