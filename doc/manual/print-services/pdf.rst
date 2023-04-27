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

.. _pdf-printer:

Generating PDF documents from print jobs
========================================

Installing the :program:`univention-printserver-pdf` package expands the print
server with a special *cups-pdf* printer type, which converts incoming print
jobs into PDF documents and adds them in a specified directory on the printer
server where they are readable for the respective user. After the installation
of the package, :command:`univention-run-join-scripts` must be run.

The ``cups-pdf:/`` protocol must be selected when creating a PDF printer
in the UMC module :guilabel:`Printers` (see :ref:`print-shares`); the
destination field remains empty.

``PDF`` must be selected as *Printer producer* and ``Generic CUPS-PDF Printer``
as *Printer model*.

The target directory for the generated PDF documents is set using the |UCSUCRV|
:envvar:`cups/cups-pdf/directory`. As standard it is set to
:file:`/var/spool/cups-pdf/%U` so that :program:`cups-pdf` uses a different
directory for each user.

Print jobs coming in anonymously are printed in the directory specified by the
|UCSUCRV| :envvar:`cups/cups-pdf/anonymous` (standard setting:
:file:`/var/spool/cups-pdf/`).

By default generated PDF documents are kept without any restrictions. If the
|UCSUCRV| :envvar:`cups/cups-pdf/cleanup/enabled` is set to ``true``, old PDF
print jobs are deleted via a Cron job. The storage time in days can be
configured using the |UCSUCRV| :envvar:`cups/cups-pdf/cleanup/keep`.
