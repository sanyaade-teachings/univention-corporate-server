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

.. _central-management-umc-login:

Login
=====

.. _umc-login:

.. figure:: /images/umc_login.*
   :alt: UCS login page

   UCS login page

UCS comes with a central login page. Logging in to the |UCSWEB| is done with the
credentials of the respective domain account. On the portal, the login process
can be started either via the user menu an then :guilabel:`Login` or by clicking
on the entry in the portal itself. If a site (e.g., a UMC module) requires a
login, it will redirect to the central login page. To sign out, the entry
:guilabel:`Logout` in the user menu can be used.

By default a login does not use single sign-on. The login can be changed to use
single sign-on (SSO) via SAML (:ref:`domain-saml`). To configure this,
``ucs-sso.[Domain name]`` must be reachable and the |UCSUCRV|
:envvar:`portal/auth-mode` has to be set to ``saml``. For the change to take
effect the portal server needs to be restarted: :command:`systemctl restart
univention-portal-server.service`. The login using the user menu has now be
changed. Portal tiles have to be adapted manually. The default portal has a SSO
login tile preconfigured which can be activated using the portal edit mode.

After successful login, a session is valid for all UCS systems of the domain as
well as for third party Apps if these support web based SSO. It is possible to
enforce a login on the local system by clicking on the link :guilabel:`Login
without Single Sign On`.

In the login mask, enter the *Username* and *Password* of the corresponding
domain account:

* When logging in with the ``Administrator`` account on a |UCSPRIMARYDN| or
  |UCSBACKUPDN|, UMC modules for the administration and configuration of the
  local system as well as UMC modules for the administration of data in the LDAP
  directory are displayed. The initial password of this account has been
  specified in the setup wizard during the installation. It corresponds to the
  initial password of the local ``root`` account. ``Administrator`` is also the
  account which should be used for the initial login at a newly installed
  |UCSPRIMARYDN|\ system.

* In some cases, it might be necessary to sign in with the system's local
  ``root`` account (see :ref:`computers-rootaccount`). This account enables
  access only to the UMC modules for the administration and configuration of the
  local system.

* When logging on with another user account, the UMC modules approved
  for the user are shown. Additional information on allowing further
  modules can be found in :ref:`delegated-administration`.

The duration of a browser session is 8 hours for the SSO login. After these, the
login process must be carried out again. For the login at the local UCS system,
the browser session will be automatically closed after an inactivity of 8 hours.

By installing a third-party application, such as :program:`privacyIDEA`, it is
possible to extend the |UCSWEB| authentication with a two-factor authentication
(2FA).
