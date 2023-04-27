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

.. _architecture-notation:

*********************
Architecture notation
*********************

A notation helps a lot to understand complex architectures and to explain the
software architecture of |UCS|. A standardized notation is key to communicate an
architecture.

This section describes the notation and elements used in this document. It's
intended to help you as reader to understand the notations. This section tries
to duplicate as little content as possible and instead provide deep links to the
corresponding resources on the internet.

.. _architecture-notation-c4-model:

C4 model
========

.. index::
   pair: architecture notation; c4 model

The document uses the C4 model in the :ref:`concepts` section.

   The C4 model is a lean graphical notation technique for modeling the
   architecture of software systems. It's based on a structural decomposition of
   a system into containers and components and relies on existing modeling
   techniques such as the Unified Modeling Language (UML) or Entity Relation
   Diagrams (ERD) for the more detailed decomposition of the architectural
   building blocks.

   — Wikipedia contributors, `"C4 model" <w-c4-model_>`_, Wikipedia, The Free Encyclopedia, (accessed January 24, 2023).

The C4 model is notation independent and provides:

#. A set of hierarchical abstractions for software systems, containers, components, and code.

#. A set of hierarchical diagrams for system context, containers, components, and code.

The C4 model is a good to learn, developer friendly approach to software
architecture diagramming. But, it comes to limits when it comes to model the
architecture. Diagramming tools draw just boxes and lines and can't answer
questions like "What dependencies does component X have?"

.. seealso::

   `The C4 model for visualizing software architecture <c4-model_>`_
      for a description of the C4 model from :cite:t:`c4-model`

.. _architecture-notation-archimate:

ArchiMate
=========

.. index::
   single: archimate; why
   single: archimate; mastering
   single: archimate; further reading
   single: archimate; reading
   pair: architecture notation; archimate

ArchiMate is a notation and modeling standard for enterprise architecture
maintained by *The OpenGroup*. This document uses the `ArchiMate® specification
3.1 <archimate-3-1-spec_>`_.

.. _architecture-notation-archimate-why:

Why ArchiMate?
--------------

   ArchiMate isn't about standard boxes and lines, it's all about a common
   language that provides the foundations for a good architecture description.

   Using the language without its notation is already of great value as it
   allows people to understand each other.

   — Jean-Baptiste Sarrodie, `"Why ArchiMate?" <archimate-why_>`_, 28. September 2018

Regarding the simplified language analogy:

* ArchiMate contains a vocabulary that covers most domains of Enterprise
  Architecture. This document focuses on technology, application and
  business.

* ArchiMate uses a grammar similar to natural language with *subject*, *verb*, and
  *object* to describe what *people* or *things* do, and adds an external, service
  oriented, view of those activities.

* The ArchiMate default notation is similar to spelling as it provides a way to
  “save ideas on paper”.

.. seealso::

   `"ArchiMate", Wikipedia, The Free Encyclopedia <w-archimate_>`_
      for an overview of the ArchiMate frameworks, language and viewpoints

.. _architecture-notation-archimate-readers-guide:

ArchiMate reader's guide
------------------------

.. index::
   single: archimate; core framework
   single: archimate; aspects
   single: archimate; active structural aspect
   single: archimate; behavior aspect
   single: archimate; passive structure aspect

This document uses the ArchiMate concepts *element*, *relationship*, and
*relationship connector* mentioned in the later sections. The following sections
provide specific links to the corresponding resources in the ArchiMate
specification with summarized definitions. They help to pick out the parts
needed to understand the notation.

To properly read ArchiMate, it's recommended to read parts of the ArchiMate
specification about the following:

#. The `ArchiMate Core Framework <archimate-core_>`_ section, that refers to the
   `layers <archimate-layers_>`_ *Business*, *Application*, and *Technology*.
   Imagine the layers as rows in a table.

#. The ArchiMate Core Framework section explains the three *Aspects*. Think of an aspect
   as columns in a table:

   * The *Active Structure Aspect* represents structural elements, the actors.
     Think of it as the subject in a natural language sentence.

   * The *Behavior Aspect* represents behavior performed by actors. Think of it
     as the verb in a natural language sentence.

   * The *Passive Structure Aspect* represents objects, the targets of the
     actors' behavior. Think of it as the object in a natural language sentence.

#. You find the ArchiMate concepts used in the document in the sections below,
   organized by layer. To read a short definition for each element, follow the
   links to the corresponding summaries in the specification.

.. seealso::

   `ArchiMate® specification 3.1 <archimate-3-1-spec_>`_
      for the complete :cite:t:`archimate-3-1`

   `Mastering ArchiMate Edition 3.1 <archimate-mastering_>`_
      for a free PDF excerpt of the book from :cite:t:`mastering-archimate`

.. _notation-archimate-business-layer:

Business layer
--------------

.. index::
   single: archimate; business layer

*Business Layer* elements model the operational organization of an enterprise in
a technology-independent manner.

For the business layer the document uses the ArchiMate concepts as shown in
:numref:`notation-archimate-business-layer-used-concepts`.

.. _notation-archimate-business-layer-used-concepts:

.. figure:: /images/ArchiMate-business-layer.*
   :width: 200 px

   ArchiMate business layer concepts used in this document

.. admonition:: Meanings in one sentence

   `Summary of Business Layer Elements <archimate-business-layer-summary_>`_
      for a table with a summary of business layer elements

.. seealso::

   `ArchiMate business layer <archimate-business-layer_>`_
      for the specification of the business layer

.. _notation-archimate-application-layer:

Application layer
-----------------

.. index::
   single: archimate; application layer

*Application Layer* elements typically model the application architecture that
describes the structure, behavior, and interaction of the applications of the
enterprise.

For the application layer the document uses the ArchiMate concepts as shown in
:numref:`notation-archimate-application-layer-used-concepts`.

.. _notation-archimate-application-layer-used-concepts:

.. figure:: /images/ArchiMate-application-layer.*
   :width: 200 px

   ArchiMate application layer concepts used in this document

.. admonition:: Meanings in one sentence

   `Summary of Application Layer Elements <archimate-application-layer-summary_>`_
      for a table with a summary of application layer elements

.. seealso::

   `ArchiMate application layer <archimate-application-layer_>`_
      for the specification of the application layer

.. _notation-archimate-technology-layer:

Technology layer
----------------

.. index::
   single: archimate; technology layer

The *Technology Layer* elements typically model the technology architecture of
the enterprise, describing the structure and behavior of the technology
infrastructure of the enterprise.

For the technology layer the document uses the ArchiMate concepts as shown in
:numref:`notation-archimate-technology-layer-used-concepts`.

.. _notation-archimate-technology-layer-used-concepts:

.. figure:: /images/ArchiMate-technology-layer.*
   :width: 200 px

   ArchiMate technology layer concepts used in this document

.. admonition:: Meanings in one sentence

   `Summary of Technology Layer Elements <archimate-technology-layer-summary_>`_
      for a table with a summary of technology layer elements

.. seealso::

   `ArchiMate technology layer <archimate-technology-layer_>`_
      for the specification of the technology layer

.. _notation-archimate-motivation-layer:

Motivation elements
-------------------

.. index::
   single: archimate; motivation elements

Motivation elements model the motivations, or reasons, that guide the design or
change of an enterprise architecture.

The motivation elements belong to the `ArchiMate full framework
<archimate-full_>`_. From the motivation elements the document uses the
ArchiMate concepts as shown in
:numref:`notation-archimate-motivation-layer-used-concepts`.

.. _notation-archimate-motivation-layer-used-concepts:

.. figure:: /images/ArchiMate-motivation-layer.*
   :width: 200 px

   ArchiMate motivation elements used in this document

.. admonition:: Meanings in one sentence

   `Summary of Motivation Elements <archimate-motivation-elements-summary_>`_
      for a table with a summary of motivation elements

.. seealso::

   `ArchiMate motivation elements <archimate-motivation-elements_>`_
      for the specification of the motivation elements

.. _notation-archimate-relationships:

Relationships
-------------

.. index::
   single: archimate; relationships

The document uses almost all relations from the ArchiMate Core framework.

.. figure:: /images/Screenshot-ArchiMate-relations-summary.png
   :width: 600 px

   Screenshot from the table with a summary of relationships in the ArchiMate
   specification

   For a link, refer to *Summary of Relationship* in the *See also* box.

As reader you may find views that don't repeat concepts and relationships in
between two concepts in focus. Such views are abstractions and they use the
derivation of relationships. ArchiMate provides derivation rules to create
abstract views.

.. admonition:: Meanings in one sentence

   `Summary of Relationships <archimate-relations-summary_>`_
      for a table with a summary of relationships

.. seealso::

   `Derivation of Relationships <archimate-relations-derivations_>`_
      for an introduction to derivation of relationships

   `ArchiMate Relationships <archimate-relations_>`_
      for the specification of relationships

   `ArchiMate Specification of Derivation Rules <archimate-derivation-rules_>`_
      for the specification of derivation rules for valid and potential
      relationships
