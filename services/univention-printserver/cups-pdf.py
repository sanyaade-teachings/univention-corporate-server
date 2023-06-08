# -*- coding: utf-8 -*-
#
# Univention Print Server
#  listener module: management of CUPS printers
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

from __future__ import absolute_import, annotations

from typing import Dict, List

import univention.config_registry
import univention.debug as ud

import listener
from listener import SetUID


description = 'Manage Samba share for CUPS pdf printer'
filter = '(objectClass=univentionShareSamba)'
attributes = ['cn', 'univentionSharePath']

sharename = "pdfPrinterShare"

fqhn = '%(hostname)s.%(domainname)s' % listener.configRegistry

# set two ucr variables (template cups-pdf) if the share for
# the pdf pseudo printer is changed


def handler(dn: str, new: Dict[str, List[bytes]], old: Dict[str, List[bytes]]) -> None:
    if new.get('cn', [b''])[0].decode('UTF-8') == sharename and new.get('univentionSharePath') and new.get('univentionShareHost'):
        path = new['univentionSharePath'][0].decode('UTF-8')
        server = new['univentionShareHost'][0].decode('ASCII')

        if fqhn == server:
            ud.debug(ud.LISTENER, ud.INFO, "cups-pdf: setting cups-pdf path to %s according to sharepath in %s on %s" % (path, sharename, server))
            list_ = [
                'cups/cups-pdf/directory=%s' % (path,),
                'cups/cups-pdf/anonymous=%s' % (path,),
            ]
            with SetUID(0):
                univention.config_registry.handler_set(list_)
