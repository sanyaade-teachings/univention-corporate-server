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

.. _print-general:

**************
Print services
**************

.. _print-services-introduction:

|UCSUCS| includes a print system, which can also be used to realize complex
environments. Printers and printer groups can be created and configured
conveniently in the UMC module :guilabel:`Printers`.

The print services are based on *CUPS (Common Unix Printing System)*. CUPS
manages print jobs in print queues and converts print jobs into the native
formats of the connected printers. The print queues are administrated via the
UMC module :guilabel:`Print jobs`, see :ref:`umc-modules-printer`.

All printers set up in CUPS can be directly used by UCS systems and are
automatically also provided for Windows computers when Samba is used.

The technical capacities of a printer are specified in so-called PPD files.
These files include for example whether a printer can print in color, whether
duplex printing is possible, whether there are several paper trays, which
resolutions are supported and which printer control languages are supported
(e.g., PCL or PostScript).

Print jobs are transformed by CUPS with the help of filters into a format that
the respective printer can interpret, for example into PostScript for a
PostScript-compatible printer.

UCS already includes a wide variety of filters and PPD files. Consequently,
most printers can be employed without the need to install additional drivers.
The setting up of additional PPD files is described in :ref:`print-ppdlisten`.

A printer can either be connected directly to the print server locally (e.g.,
via the USB port or a parallel port) or communicate with a printer via remote
protocols (e.g., TCP/IP compatible printers, which are connected via ``IPP`` or
``LPD``).

Network printers with their own IP address should be registered in the UMC
module :guilabel:`Computers` as an IP client (see :ref:`system-roles`).

CUPS offers the possibility of defining printer groups. The included printers
are used employed alternating, which allows automatic load distribution between
neighboring printers.

Print shares from Windows systems can also be integrated in the CUPS print
server, see :ref:`print-shares`.

.. toctree::
   :caption: Chapter contents:

   install
   configuration
   share
   group
   umc
   pdf
   windows-clients
   ppd
