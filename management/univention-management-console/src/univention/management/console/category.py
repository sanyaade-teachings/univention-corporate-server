# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMC category definitions
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2006-2023 Univention GmbH
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

"""
Category definitions
====================

The UMC server provides the possibility to define categories used to
sort the available UMC modules into groups. Each module can be in as
many groups as desired.

The category definitions are stored in XML files that structured as in
the following example

.. code-block:: xml

    <?xml version="1.0" encoding="UTF-8"?>
    <umc version="2.0">
        <categories>
            <category id="id1">
                <name>Category 1</name>
            </category>
            <category id="id2">
                <name>Category 2 on {hostname}.{domainname}</name>
            </category>
        </categories>
    </umc>

Each file can define several categories. For each of these
categories an unique identifier and the english description must be
specified. The translations are stored in extra po files that are
generated by the UMC build tools.

Within the description of a category UCR variable names can be used that
will be substituted by the value. Therefore the name of the variables
must be given in curly braces {VARIABLE}.
"""

import os
import sys
import xml.etree.cElementTree as ET
import xml.parsers.expat

from .log import RESOURCES


class XML_Definition(ET.ElementTree):
    """Represents a category definition."""

    def __init__(self, root=None, filename=None, domain=None,):
        ET.ElementTree.__init__(self, element=root, file=filename,)
        self.domain = domain

    @property
    def name(self):
        """Returns the descriptive name of the category"""
        return self.find('name').text

    @property
    def id(self):
        """Returns the unique identifier of the category"""
        return self._root.get('id')

    @property
    def icon(self):
        return self._root.get('icon')

    @property
    def color(self):
        return self._root.get('color')

    @property
    def priority(self):
        """
        Returns the priority of the category. If no priority is
        defined the default priority of -1 is returned. None is returned
        if the specified priority is not a valid float

        :rtype: float or None
        """
        try:
            return float(self._root.get('priority', -1,))
        except ValueError:
            RESOURCES.warn('No valid number type for property "priority": %s' % self._root.get('priority'))
        return None

    def json(self):
        """
        Returns a JSON compatible representation of the category

        :rtype: dict
        """
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'color': self.color,
            'priority': self.priority,
        }


class Manager(dict):
    """This class manages all available categories."""

    DIRECTORY = os.path.join(sys.prefix, 'share/univention-management-console/categories',)

    def __init__(self):
        dict.__init__(self)

    def all(self):
        return [x.json() for x in self.values()]

    def load(self):
        self.clear()
        RESOURCES.info('Loading categories ...')
        for filename in os.listdir(Manager.DIRECTORY):
            if not filename.endswith('.xml'):
                RESOURCES.info('Found file %s with wrong suffix' % filename)
                continue
            try:
                definitions = ET.ElementTree(file=os.path.join(Manager.DIRECTORY, filename,))
                categories = definitions.find('categories')
                if categories is None:
                    continue
                i18nDomain = categories.get('domain')
                for category_elem in definitions.findall('categories/category'):
                    category = XML_Definition(root=category_elem, domain=i18nDomain,)
                    self[category.id] = category
                RESOURCES.info('Loaded categories from %s' % filename)
            except (xml.parsers.expat.ExpatError, ET.ParseError) as exc:
                RESOURCES.warn('Failed to parse category file %s: %s' % (filename, exc))
                continue
