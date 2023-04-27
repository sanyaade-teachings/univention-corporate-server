.. Like what you see? Join us!
.. https://www.univention.com/about-us/careers/vacancies/
..
.. Copyright (C) 2021-2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only
..
.. https://www.univention.com/
..
.. All rights reserved.
..
.. The source code of this program is made available under the terms of
.. the GNU Affero General Public License v3.0 only (AGPL-3.0-only) as
.. published by the Free Software Foundation.
..
.. Binary versions of this program provided by Univention to you as
.. well as other copyrighted, protected or trademarked materials like
.. Logos, graphics, fonts, specific documentations and configurations,
.. cryptographic keys etc. are subject to a license agreement between
.. you and Univention and not subject to the AGPL-3.0-only.
..
.. In the case you use this program under the terms of the AGPL-3.0-only,
.. the program is provided in the hope that it will be useful, but
.. WITHOUT ANY WARRANTY; without even the implied warranty of
.. MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
.. Affero General Public License for more details.
..
.. You should have received a copy of the GNU Affero General Public
.. License with the Debian GNU/Linux or Univention distribution in file
.. /usr/share/common-licenses/AGPL-3; if not, see
.. <https://www.gnu.org/licenses/agpl-3.0.txt>.

.. _domain-kerberos:

Kerberos
========

Kerberos is an authentication framework the purpose of which is to
permit secure identification in the potentially insecure connections of
decentralized networks. In Kerberos, all clients use a foundation of
mutual trust, the *Key Distribution Center* (KDC).
A client authenticates at this KDC and receives an authentication token,
the so-called ticket which can be used for authentication within the
Kerberos environment (the so-called Kerberos realm). The name of the
Kerberos realm is configured as part of the installation of the
|UCSPRIMARYDN| and stored in the |UCSUCRV| :envvar:`kerberos/realm`.
It is not possible to change the name of the Kerberos realm at a later
point in time.

Tickets have a standard validity period of 8 hours; this is why it is
vital for a Kerberos domain to have the system time synchronized for all
the systems belonging to the Kerberos realm.

|UCSUCS| uses the Heimdal Kerberos implementation. An independent Heimdal
service is started on UCS Directory Nodes without Samba/AD, while
Kerberos is provided by a Heimdal version integrated in Samba on
Samba/AD DCs. In a environment composed of UCS Directory Nodes without
Samba/AD and Samba/AD domain controllers both Kerberos environments are
based on identical data (these are synchronized between Samba/AD and
OpenLDAP via the Univention S4 connector (see
:ref:`windows-s4-connector`)).

.. _domain-kerberos-kdc-selection:

KDC selection
-------------

As standard, the KDC is selected via a DNS service record. The KDC used
by a system can be reconfigured using the |UCSUCRV|
:envvar:`kerberos/kdc`. If Samba/AD is installed on a system in
the domain, the service record is reconfigured so that only the
Samba/AD-based KDCs are offered. In a mixed environment it is
recommended only to use the Samba/AD KDCs.

.. _domain-kerberos-admin-server:

Kerberos admin server
---------------------

The Kerberos admin server, on which the administrative settings of the
domain can be made, runs on the |UCSPRIMARYDN|. Most of the settings in
Univention Corporate Server are taken from the LDAP directory, so that
the major remaining function is changing passwords. This can be achieved
by means of the Tool :command:`kpasswd`; the passwords are
then changed in the LDAP too. The Kerberos admin server can be
configured on a system via the |UCSUCRV|
:envvar:`kerberos/adminserver`.
