# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright (C) 2008-2023 Univention GmbH
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

from __future__ import annotations

import re
import time
from os import listdir
from os.path import join, normpath
from typing import List

import univention.ucslint.base as uub


RE_SKIP = re.compile(
    '|'.join((
        'temporary wrapper script for',
        'Generated by ltmain.sh',
        'This file is maintained in Automake',
    )))
RE_HASHBANG = re.compile(r'^#!')
DEP5 = "Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/"
# Copyright (C) 2004-2023 Univention GmbH
# Copyright (C) 2004-2023 Univention GmbH
# Copyright 2008 by
# Copyright: 2004-2023 Univention GmbH
# SPDX-FileCopyrightText: 2014-2023 Univention GmbH
RE_COPYRIGHT_VERSION = re.compile(r'(?:Copyright(?:\s+\(C\)|:)?|SPDX-FileCopyrightText:)\s+([0-9, -]+)\s+(?:by|Univention\s+GmbH)')


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

    def getMsgIds(self) -> uub.MsgIds:
        return {
            '0010-1': (uub.RESULT_WARN, 'failed to open file'),
            '0010-2': (uub.RESULT_ERROR, 'file contains no copyright text block'),
            '0010-3': (uub.RESULT_INFO, 'copyright is outdated'),
            '0010-4': (uub.RESULT_ERROR, 'cannot find copyright line containing year'),
            '0010-5': (uub.RESULT_ERROR, 'file debian/copyright is missing'),
            '0010-6': (uub.RESULT_WARN, 'debian/copyright is not machine-readable DEP-5'),
        }

    def check(self, path: str) -> None:
        super().check(path)

        check_files: List[str] = []

        # check if copyright file is missing
        fn = normpath(join(path, 'debian', 'copyright'))
        try:
            with open(fn) as stream:
                line = stream.readline().rstrip()
                if line != DEP5:
                    self.addmsg('0010-6', 'not machine-readable DEP-5', fn)
        except OSError:
            self.addmsg('0010-5', 'file is missing', fn)

        # looking for files below debian/
        for f in listdir(normpath(join(path, 'debian'))):
            fn = normpath(join(path, 'debian', f))
            if f.endswith(('.preinst', '.postinst', '.prerm', '.postrm')) or f in ['preinst', 'postinst', 'prerm', 'postrm', 'copyright']:
                check_files.append(fn)

        # looking for Python files
        for fn in uub.FilteredDirWalkGenerator(path, reHashBang=RE_HASHBANG, readSize=100):
            check_files.append(fn)  # noqa: PERF402

        # check files for copyright
        for fn in check_files:
            try:
                with open(fn) as fd:
                    content = fd.read()
            except (OSError, UnicodeDecodeError):
                self.addmsg('0010-1', 'failed to open and read file', fn)
                continue
            self.debug('testing %s' % fn)

            if RE_SKIP.search(content):
                continue

            if not self.is_agpl3(content):
                self.addmsg('0010-2', 'file contains no copyright text block', fn)
                continue

            # copyright text block is present - lets check if it's outdated
            match = RE_COPYRIGHT_VERSION.search(content)
            if not match:
                self.addmsg('0010-4', 'cannot find copyright line containing year', fn)
            else:
                years = match.group(1)
                current_year = str(time.localtime()[0])
                if current_year not in years:
                    self.debug(f'Current year={current_year}  years="{years}"')
                    self.addmsg('0010-3', 'copyright line seems to be outdated', fn)

    SPDX = "SPDX-License-Identifier: AGPL-3.0-only"
    AGPL = (
        'under the terms of the GNU Affero General Public License version 3',
        'Binary versions of this',
        'provided by Univention to you as',
        'cryptographic keys etc. are subject to a license agreement between',
        'the terms of the GNU AGPL V3',
        'You should have received a copy of the GNU Affero General Public',
    )

    def is_agpl3(self, content: str) -> bool:
        if self.SPDX in content:
            return True

        for line in self.AGPL:
            if line not in content:
                self.debug('Missing copyright string: %s' % line)
                return False

        return True
