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

.. _concept-role:

Role concept
============

|UCS| uses a role concept to assign different roles that include certain tasks
to the systems in a domain.

Primary Directory Node
----------------------

.. index::
   single: domain roles; Primary Directory Node
   single: Primary Directory Node

A UCS system with the role *Primary Directory Node* is the first, the primary,
domain node in a domain. It's the only system with write permissions to the
central domain database and performs all write requests regarding data for the
domain database. Only one system in the domain can have the Primary Directory
Node role.

Backup Directory Node
---------------------

.. index::
   single: domain roles; Backup Directory Node
   single: Backup Directory Node

A UCS system with the role *Backup Directory Node* has a complete read-only copy
of the domain database, including security certificates. More than one UCS
system can have the Backup Directory Node role. In case the Primary Directory
Node is unavailable, recovery is impossible or needs too much time, an
administrator can promote a UCS system in the role Backup Directory Node to a
Primary Directory Node. The promotion can't be reversed.

.. seealso::

   :ref:`uv-manual:domain-backup2master`
      for details on the promotion process of a UCS Backup Directory Node in
      :cite:t:`ucs-manual`.

Replica Directory Node
----------------------

.. index::
   single: domain roles; Replica Directory Node
   single: Replica Directory Node

UCS systems with the role *Replica Directory Node* have a complete read-only
copy of the domain database. Administrators can't promote Replicate Directory
Nodes to the Primary Directory Node role or any other role unlike the Backup
Directory Node.

A Replica Directory Node optionally allows selective replication, a form of data
synchronization that replicates only a subset of the domain database. Selective
replication in UCS helps with data minimization, domain protection and
permission enforcement.

For example, imagine an organization with office locations in cities like Berlin
and Bremen. Each location has a Replica Directory Node as domain node. The
Replica Directory Nodes only replicate domain objects like users, groups, and
printers that are relevant for their respective location. They don't store
objects assigned to other locations.

Replica Directory Nodes are ideally suited as dedicated systems for load
intensive services with permanent read operations to the domain database because
the read operations run locally instead of across the computer network.

Managed Node
------------

.. index::
   single: domain roles; Managed Node
   single: Managed Node

UCS systems with the role *Managed Node* don't have any copy of the domain
database. Services on Managed Nodes read domain information over the network
from either the Primary Directory Node or from one of the Backup Directory
Nodes.

Clients
-------

Clients are systems in the domain's trust context. They don't have a special
role regarding domain services as the other roles described before. In most
cases they consume services offered by the domain or other systems.

UCS offers dedicated client roles for desktop systems like Ubuntu, other Linux
desktops and macOS. UCS manages IP addresses and DNS entries for systems like
network printers and routers with the *IP client* role.

For Microsoft Windows related systems, UCS offers the roles *Domain Trust
Account*, *Windows Domaincontroller* and *Windows Workstation / Server*.

.. seealso::

   :ref:`uv-manual:system-roles`
      For more information about the differences of these roles in
      :cite:t:`ucs-manual`
