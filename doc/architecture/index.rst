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

.. _introduction:

************
Introduction
************

Welcome to the architecture documentation of |UCS|.

This document doesn't cover installation, the usage of UCS or parts of the
product. For instructions about how to install and use UCS, see
:cite:t:`ucs-manual`.

.. TODO Remove this sentence once the whole document is done.

The document is released iteratively after each part is finished. The beginning
is at the first, high level.

Your feedback is welcome and highly appreciated. If you have comments, suggestions,
or criticism, please `send your feedback
<https://www.univention.com/feedback/?architecture=generic>`_ for document
improvement.

For feedback on single sections, use the feedback link next to the section
title.

Audience
========

This document is for consultants, administrators, solution architects, software
developers and system engineers. It describes the technical architecture of UCS
on three different detail levels.

The first, high level, :ref:`positions UCS in the known IT world
<positioning>` and describes the :ref:`concepts <concepts>`. This view helps
readers to understand the principles of UCS. Chapters 2 and 3 assume you are
familiar with information technology in general and that you have heard of
computer network building blocks and software.

.. TODO : Enable the references, once the sections are written:
   """covers the :ref:`product components <product-components>` and the :ref:`numerous
   services <services>` UCS offers to IT infrastructures. Software developers and"""

The second, medium level, is for administrators and solution architects. It
covers the product components and the numerous services UCS offers to IT
infrastructures. You read about the user facing product components and what
services UCS runs. You learn what open source software contributes to the
capability of UCS and how it interoperates together.

Software developers and system engineers get an overview of the technical parts.

A general understanding of Linux operating systems for servers and IT
administration are beneficial for understanding.

For notation, the document uses the *C4 model* notation and the *ArchiMate*
notation. For more information, refer to :ref:`architecture-notation`.

.. TODO : Enable the references, once the sections are written:
   """The third, low level is about the :ref:`libraries <libraries>`, :ref:`internal
   systems and storage <systems-storage>`. It describes the pieces a software"""

The third, low level is about the libraries, internal systems and storage. It
describes the pieces a software developer and system engineer needs to know to
contribute to UCS. General knowledge of software architecture and software
engineering are helpful at this level.

Learning objectives
===================

After reading this document you have a broad understanding of the UCS
architecture. It equips consultants, administrators, and solution architects to
better plan their IT environment with UCS. It enables software developers and
system engineers to get familiar with software development for UCS.
