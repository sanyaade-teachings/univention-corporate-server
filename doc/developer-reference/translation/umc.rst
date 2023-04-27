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

.. _translation-umc:

Create a translation package for UCS
====================================

.. index::
   single: translation
   see: localisation; translation

UCS provides builtin English and German localization and a French translation package. Univention provides a set of tools
that facilitates the creation of translation packages. Translation packages can
provide translations for all translatable strings of UCS for a specific
language. The |UCSUMC|, more specifically its packages, contains the largest
share of translatable strings. This section describes all necessary steps to create a translation package for
UCS.

.. _translation-umc-preparation:

Install needed tools
--------------------

The package :program:`univention-l10n-dev` contains all tools required to set up
and update a translation package. It requires some additional Debian tools to
build the package. Run the following command on UCS to install all needed
packages.

.. code-block:: console

   $ sudo univention-install univention-l10n-dev dpkg-dev git


.. _translation-umc-checkout:

Obtain a current checkout of the UCS Git repository
---------------------------------------------------

The Git repository is later processed to get initial files for a new
translation (often referred to as PO file or Portable Objects).

.. code-block:: console

   $ mkdir ~/translation
   $ cd ~/translation
   $ git clone \
     --single-branch \
     --depth 1 \
     --shallow-submodules \
     https://github.com/univention/univention-corporate-server


.. _translation-umc-create-package:

Create translation package
--------------------------

To create a translation package, for example for French, in the current working
directory, the following command must be executed:

.. code-block:: console

   $ cd ~/translation
   $ univention-ucs-translation-build-package \
     --source ~/translation/univention-corporate-server \
     --languagecode fr \
     --locale fr_FR.UTF-8:UTF-8 \
     --language-name French


This creates a new directory :file:`~/translation/univention-l10n-fr/` which
contains a Debian source package of the same name. It includes all source and
target files for the translation.

.. _translation-umc-translate:

Edit translation files
----------------------

The translation source files (:file:`.po` files) are located below the directory
:file:`~/translation/univention-l10n-fr/fr`. Each file should be edited to
create the translation. Refer to :ref:`editing-translation-files` for detailed information.

.. _translation-umc-update-package:

Update the translation package
------------------------------

First update the Git repository:

.. code-block:: console

   $ cd ~/translation/univention-corporate-server
   $ git pull --rebase


If changes affecting translations are made in the Git repository, existing
translation packages need to be updated to reflect those changes. Given a path
to an updated Git checkout, :command:`univention-ucs-translation-merge` can
update a previously created translation source package.

The following example updates the translation package
:program:`univention-l10n-fr`:

.. code-block:: console

   $ univention-ucs-translation-merge \
     ~/translation/univention-corporate-server \
     ~/translation/univention-l10n-fr


.. _translation-umc-build-package:

Build the translation package
-----------------------------

Before using the new translation, the Debian package has to be built and
installed. This can be done with the following commands:

.. code-block:: console

   $ cd ~/translation/univention-l10n-fr
   $ sudo apt-get build-dep .
   $ dpkg-buildpackage -uc -us -b -rfakeroot
   $ sudo dpkg -i ../univention-l10n-fr_*.deb


After logging out of the |UCSUMC| the new language should now be selectable in
the |UCSUMC| login window. Untranslated strings are still shown in their
original language, that is, in English.

