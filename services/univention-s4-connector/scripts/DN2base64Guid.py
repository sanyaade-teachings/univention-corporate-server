#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  Convert S4 DN to base64 objectGuid as used in s4cache.sqlite
#
# Copyright 2014-2024 Univention GmbH
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

import samba
import sys
import ldb
import base64
from optparse import OptionParser

from samba import dsdb
from samba.samdb import SamDB
from samba.param import LoadParm
from samba.auth import system_session
from samba.credentials import Credentials

if __name__ == '__main__':
	parser = OptionParser(usage='DN2base64Guid.py dn')
	(options, args) = parser.parse_args()

	if len(args) != 1:
		parser.print_help()
		sys.exit(2)

	dn = args[0]

	lp = LoadParm()
	creds = Credentials()
	creds.guess(lp)
	samdb = SamDB(url='/var/lib/samba/private/sam.ldb', session_info=system_session(), credentials=creds, lp=lp)

	domain_dn = samdb.domain_dn()
	res = samdb.search(dn, scope=ldb.SCOPE_BASE, attrs=["objectGuid"])

	for msg in res:
		guid = msg.get("objectGuid", idx=0)
		print base64.encodestring(guid),

	sys.exit(0)
