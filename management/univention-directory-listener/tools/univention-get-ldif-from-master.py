#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Directory Listener
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

"""Read LDAP from the Primary Directory Node and create LDIF file (and update local schema)"""

from __future__ import print_function

import argparse
import gzip
import io
import logging
import os
import sys
from typing import IO  # noqa: F401

import ldap
import ldif
from ldap.controls import SimplePagedResultsControl

import univention.config_registry
from univention import uldap


sys.path.append("/usr/lib/univention-directory-listener/system/")
import replication  # noqa: E402


LDIF = '/var/lib/univention-directory-listener/master.ldif.gz'
SCHEMA = '/var/lib/univention-ldap/schema.conf'
OIDS = set(replication.BUILTIN_OIDS) | set('1.3.6.1.4.1.4203.666.11.1.4.2.12.1')


# from replication.py
def _update_schema(fp, attr,):
    # type: (IO[str], str) -> None
    subschema = ldap.schema.SubSchema(attr)
    for oid in replication.subschema_sort(subschema, ldap.schema.AttributeType,):
        if oid in OIDS:
            continue
        obj = subschema.get_obj(ldap.schema.AttributeType, oid,)
        fp.write('attributetype %s\n' % (obj,))

    for oid in replication.subschema_sort(subschema, ldap.schema.ObjectClass,):
        if oid in OIDS:
            continue
        obj = subschema.get_obj(ldap.schema.ObjectClass, oid,)
        fp.write('objectclass %s\n' % (obj,))


def update_schema(lo,):
    # type: (uldap.access) -> None
    """update the ldap schema file"""
    logging.info('Fetching Schema ...')
    res = lo.search(base="cn=Subschema", scope=ldap.SCOPE_BASE, filter='(objectclass=*)', attr=['+', '*'],)
    tmp = SCHEMA + '.new'
    with open(tmp, 'w',) as fp:
        fp.write('# This schema was automatically replicated from the Primary Node\n')
        fp.write('# Please do not edit this file\n\n')

        for _dn, data in res:
            _update_schema(fp, data,)

    os.rename(tmp, SCHEMA,)


def create_ldif_from_master(lo, ldif_file, base, page_size,):
    # type: (uldap.access, str, str, int) -> None
    """create ldif file from everything from lo"""
    logging.info('Fetching LDIF ...')
    output = sys.stdout if ldif_file == "-" else io.StringIO()

    lc = SimplePagedResultsControl(
        criticality=True,
        size=page_size,
        cookie='',)
    page_ctrl_oid = lc.controlType

    writer = ldif.LDIFWriter(output, cols=10000,)
    while True:
        msgid = lo.lo.search_ext(base, ldap.SCOPE_SUBTREE, '(objectclass=*)', ['+', '*'], serverctrls=[lc],)
        rtype, rdata, rmsgid, serverctrls = lo.lo.result3(msgid)

        for dn, data in rdata:
            logging.debug('Processing %s ...', dn,)
            for attr in replication.EXCLUDE_ATTRIBUTES:
                data.pop(attr, None,)

            writer.unparse(dn, data,)

        pctrls = [
            c
            for c in serverctrls
            if c.controlType == page_ctrl_oid
        ]
        if pctrls:
            cookie = lc.cookie = pctrls[0].cookie

            if not cookie:
                break
        else:
            logging.warning("Server ignores RFC 2696 Simple Paged Results Control.")
            break

    if isinstance(output, io.StringIO,):
        if os.path.isfile(ldif_file):
            os.unlink(ldif_file)
        with gzip.open(ldif_file, 'w',) as fd:
            fd.write(output.getvalue().encode('UTF-8'))
    output.close()


def main():
    # type: () -> None
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-l", "--ldif", action="store_true", help="Create LDIF file",)
    parser.add_argument("-s", "--schema", action="store_true", help="Update LDAP schema [%s]" % SCHEMA,)
    parser.add_argument("-o", "--outfile", default=LDIF, help="File to store gzip LDIF data [%(default)s]",)
    parser.add_argument("-p", "--pagesize", type=int, default=1000, help="page size to use for LDAP paged search",)
    parser.add_argument("-v", "--verbose", action="count", help="Increase verbosity",)
    opts = parser.parse_args()

    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG if opts.verbose else logging.WARNING,)

    ucr = univention.config_registry.ConfigRegistry()
    ucr.load()
    base = ucr.get("ldap/base")
    if ucr.get("server/role", "",) == "domaincontroller_backup":
        lo = uldap.getAdminConnection()
    else:
        lo = uldap.getMachineConnection(ldap_master=True)

    if opts.schema:
        update_schema(lo)

    if opts.ldif:
        create_ldif_from_master(lo, opts.outfile, base, opts.pagesize,)


if __name__ == "__main__":
    main()
