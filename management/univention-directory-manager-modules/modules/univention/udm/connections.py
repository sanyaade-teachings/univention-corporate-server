# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2018-2024 Univention GmbH
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
# you and Univention.
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


import sys

import ldap
from ldap.filter import filter_format

import univention.admin.uexceptions
import univention.admin.uldap
import univention.config_registry

from .exceptions import ConnectionError


class LDAP_connection(object):
    """Caching LDAP connection factory."""

    _ucr = None
    _connection_admin = None
    _connection_account = {}

    @classmethod
    def _clear(cls):
        # used in tests
        cls._ucr = None
        cls._connection_admin = None
        cls._connection_account.clear()

    @classmethod
    def _wrap_connection(cls, func, **kwargs):
        try:
            return func(**kwargs)
        except OSError:
            raise ConnectionError('Could not read secret file').with_traceback(sys.exc_info()[2])
        except univention.admin.uexceptions.authFail:
            raise ConnectionError('Credentials invalid').with_traceback(sys.exc_info()[2])
        except ldap.INVALID_CREDENTIALS:
            raise ConnectionError('Credentials invalid').with_traceback(sys.exc_info()[2])
        except ldap.CONNECT_ERROR:
            raise ConnectionError('Connection refused').with_traceback(sys.exc_info()[2])
        except ldap.SERVER_DOWN:
            raise ConnectionError('The LDAP Server is not running').with_traceback(sys.exc_info()[2])

    @classmethod
    def get_admin_connection(cls):
        if not cls._connection_admin:
            cls._connection_admin, po = cls._wrap_connection(univention.admin.uldap.getAdminConnection)
        return cls._connection_admin

    @classmethod
    def get_machine_connection(cls, ldap_master=True):
        # do not cache the machine connection as this breaks on server-password-change
        co, po = cls._wrap_connection(univention.admin.uldap.getMachineConnection, ldap_master=ldap_master)
        return co

    @classmethod
    def get_credentials_connection(
            cls,
            identity,
            password,
            base=None,
            server=None,
            port=None,
    ):
        if not cls._ucr:
            cls._ucr = univention.config_registry.ConfigRegistry()
            cls._ucr.load()

        if '=' not in identity:
            lo = cls.get_machine_connection()
            dns = lo.searchDn(filter_format('uid=%s', (identity,)))
            try:
                identity = dns[0]
            except IndexError:
                raise ConnectionError('Cannot get DN for username').with_traceback(sys.exc_info()[2])
        access_kwargs = {'binddn': identity, 'bindpw': password, 'base': base or cls._ucr['ldap/base']}
        if server:
            access_kwargs['host'] = server
        if port:
            access_kwargs['port'] = port
        key = (identity, password, server, port, base)
        if key not in cls._connection_account:
            cls._connection_account[key] = cls._wrap_connection(univention.admin.uldap.access, **access_kwargs)
        return cls._connection_account[key]
