# -*- coding: utf-8 -*-
#
# Univention SAML
#  listener module: management of SAML service providers
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2013-2023 Univention GmbH
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

from __future__ import absolute_import, annotations

import glob
import os
import os.path
import xml.etree.ElementTree
from subprocess import PIPE, Popen
from tempfile import NamedTemporaryFile
from typing import Dict, List, Tuple

import univention.debug as ud
from univention.saml.lib import php_array, php_bool, php_string

import listener


description = 'Manage simpleSAMLphp service providers'
filter = '(objectClass=univentionSAMLServiceProvider)'

# based on /usr/share/simplesamlphp/www/admin/metadata-converter.php
raw_metadata_generator = r'''<?php
set_error_handler(function($errno, $errstr, $errfile, $errline) {
    throw new ErrorException($errstr, 0, $errno, $errfile, $errline);
});

$xmldata = file_get_contents("php://stdin");
require_once('/usr/share/simplesamlphp/lib/_autoload.php');
use Symfony\Component\VarExporter\VarExporter;
\SimpleSAML\Utils\XML::checkSAMLMessage($xmldata, 'saml-meta');
$entities = \SimpleSAML\Metadata\SAMLParser::parseDescriptorsString($xmldata);
foreach ($entities as $entityId => &$entity) {
    $entityMetadata = $entity->getMetadata20SP();
    unset($entityMetadata['entityDescriptor']);
    print('$metadata[' . var_export($entityId, true) . '] = ' . VarExporter::export($entityMetadata) . ";\n");
}
'''
sp_config_dir = '/etc/simplesamlphp/metadata.d'
include_file = '/etc/simplesamlphp/metadata/metadata_include.php'


def ldap_attribute_join(old: List[str | List[str]],) -> List[Tuple[str, str]]:
    result_keys: Dict[str, str] = {}
    for attr in old:
        if attr[0] not in result_keys.keys() and len(attr) > 1:
            result_keys[attr[0]] = "%s" % (attr[1],)
        elif attr[0] in result_keys.keys() and len(attr) > 1:
            result_keys[attr[0]] += ", %s" % (attr[1],)
        elif len(attr) == 1:
            result_keys[attr[0]] = ''
    return [(key, value) for key, value in result_keys.items()]


def handler(dn: str, new: Dict[str, List[bytes]], old: Dict[str, List[bytes]],) -> None:
    listener.setuid(0)
    try:
        if old and old.get('SAMLServiceProviderIdentifier'):
            # delete old service provider config file
            old_filename = os.path.join(sp_config_dir, '%s.php' % old.get('SAMLServiceProviderIdentifier')[0].decode('ASCII').replace('/', '_',),)
            if os.path.exists(old_filename):
                ud.debug(ud.LISTENER, ud.INFO, 'Deleting old SAML SP Configuration file %s' % old_filename,)
                try:
                    os.unlink(old_filename)
                except IOError as exc:
                    ud.debug(ud.LISTENER, ud.ERROR, 'Deleting failed: %s' % (exc,),)

        if new and new.get('SAMLServiceProviderIdentifier') and new.get('isServiceProviderActivated')[0] == b"TRUE":
            # write new service provider config file
            filename = os.path.join(sp_config_dir, '%s.php' % new.get('SAMLServiceProviderIdentifier')[0].decode('ASCII').replace('/', '_',),)
            ud.debug(ud.LISTENER, ud.INFO, 'Writing to SAML SP Configuration file %s' % filename,)
            write_configuration_file(dn, new, filename,)

        with open(include_file, 'w',) as fd:
            fd.write('<?php\n')
            for filename in glob.glob(os.path.join(sp_config_dir, '*.php',)):
                fd.write("require_once(%s);\n" % (php_string(filename),))
    finally:
        listener.unsetuid()


def write_configuration_file(dn: str, new: Dict[str, List[bytes]], filename: str,) -> bool:
    if new.get('serviceProviderMetadata') and new['serviceProviderMetadata'][0]:
        metadata = new['serviceProviderMetadata'][0]
        try:
            root = xml.etree.ElementTree.fromstring(metadata.decode('ASCII'))  # noqa: S314
            entityid = root.get('entityID')
        except xml.etree.ElementTree.ParseError as exc:
            ud.debug(ud.LISTENER, ud.ERROR, 'Parsing metadata failed: %s' % (exc,),)
            return False
    else:
        metadata = None
        entityid = new.get('SAMLServiceProviderIdentifier')[0].decode('ASCII')

    rawsimplesamlSPconfig = new.get('rawsimplesamlSPconfig', [b''],)[0].decode('ASCII')
    fd = open(filename, 'w',)

    if rawsimplesamlSPconfig:
        fd.write(rawsimplesamlSPconfig)
    else:
        fd.write("<?php\n")
        fd.flush()
        fd.write('$memberof = "False";\n')
        fd.write("if(file_exists('/etc/simplesamlphp/serviceprovider_enabled_groups.json')){\n")
        fd.write("	$samlenabledgroups = json_decode(file_get_contents('/etc/simplesamlphp/serviceprovider_enabled_groups.json'), true);\n")
        fd.write("	if(array_key_exists(%s, $samlenabledgroups) and isset($samlenabledgroups[%s])){\n" % (php_string(dn), php_string(dn)))
        fd.write("		$memberof = $samlenabledgroups[%s];\n" % (php_string(dn)))
        fd.write("	}\n")
        fd.write("}\n")

        if metadata:
            with NamedTemporaryFile(mode='w+') as temp:
                temp.write(raw_metadata_generator)
                temp.flush()

                process = Popen(['/usr/bin/php', temp.name, entityid], stdout=fd, stderr=PIPE, stdin=PIPE,)
                stdout, stderr = process.communicate(metadata)
                if process.returncode != 0:
                    ud.debug(ud.LISTENER, ud.ERROR, 'Failed to create %s: %s' % (filename, stderr.decode('UTF-8', 'replace',)),)
            fd.write("$further = array(\n")
        else:
            fd.write('$metadata[%s] = array(\n' % php_string(entityid))
            fd.write("	'AssertionConsumerService' => %s,\n" % php_array(new.get('AssertionConsumerService')))
            if new.get('singleLogoutService'):
                fd.write("	'SingleLogoutService' => %s,\n" % php_array(new.get('singleLogoutService')))

        if new.get('signLogouts') and new.get('signLogouts')[0] == b"TRUE":
            fd.write("	'sign.logout' => TRUE,\n")
        if new.get('NameIDFormat'):
            fd.write("	'NameIDFormat' => %s,\n" % php_string(new.get('NameIDFormat')[0]))
        if new.get('simplesamlNameIDAttribute'):
            fd.write("	'simplesaml.nameidattribute' => %s,\n" % php_string(new.get('simplesamlNameIDAttribute')[0]))
        if new.get('simplesamlAttributes'):
            fd.write("	'simplesaml.attributes' => %s,\n" % php_bool(new.get('simplesamlAttributes')[0]))
        simplesamlLDAPattributes: List[str | List[str]] = []
        if new.get('simplesamlAttributes') and new.get('simplesamlAttributes')[0] == b"TRUE":
            simplesamlLDAPattributes = list(dict.fromkeys(entry.decode('ASCII').split('=', 1,)[0].strip() for entry in new.get('simplesamlLDAPattributes', [],)))
            if new.get('simplesamlNameIDAttribute') and new.get('simplesamlNameIDAttribute')[0].decode('ASCII') not in simplesamlLDAPattributes:
                simplesamlLDAPattributes.append(new.get('simplesamlNameIDAttribute')[0].decode('ASCII'))
            fd.write("	'attributes' => %s,\n" % php_array(simplesamlLDAPattributes))
            simplesamlLDAPattributes = [entry.decode('ASCII').split('=', 1,) for entry in new.get('simplesamlLDAPattributes', [],) if entry.split(b'=', 1,)[0] and len(entry.split(b'=', 1,)) > 1 and entry.split(b'=', 1,)[1] and entry.split(b'=', 1,)[0] != entry.split(b'=', 1,)[1]]
        if new.get('attributesNameFormat'):
            fd.write("	'attributes.NameFormat' => %s,\n" % php_string(new.get('attributesNameFormat')[0]))
        if new.get('serviceproviderdescription'):
            fd.write("	'description' => %s,\n" % php_string(new.get('serviceproviderdescription')[0]))
        if new.get('serviceProviderOrganizationName'):
            fd.write("	'OrganizationName' => %s,\n" % php_string(new.get('serviceProviderOrganizationName')[0]))
        if new.get('privacypolicyURL'):
            fd.write("	'privacypolicy' => %s,\n" % php_string(new.get('privacypolicyURL')[0]))

        fd.write("	'assertion.lifetime' => %d,\n" % (int(new.get('assertionLifetime', [b'300'],)[0].decode('ASCII')),))
        fd.write("	'authproc' => array(\n")
        if not metadata:  # TODO: make it configurable
            # make sure that only users that are enabled to use this service provider are allowed
            fd.write("		10 => array(\n")
            fd.write("			'class' => 'authorize:Authorize',\n")
            fd.write("			'regex' => FALSE,\n")
            fd.write("			'case_insensitive_attributes' => array('memberOf', 'enabledServiceProviderIdentifier'),\n")
            fd.write("			'enabledServiceProviderIdentifier' => %s,\n" % php_array([dn]))
            fd.write("			'memberOf' => $memberof,\n")
            fd.write("		),\n")
            if simplesamlLDAPattributes:
                fd.write("		50 => array(\n			'class' => 'core:AttributeMap',\n")
                for attr in ldap_attribute_join(simplesamlLDAPattributes):
                    if ',' in attr[1]:
                        fd.write("			%s => %s,\n" % (php_string(attr[0]), php_array(attr[1].split(','))))
                    else:
                        fd.write("			%s => %s,\n" % (php_string(attr[0]), php_string(attr[1])))
                fd.write("		),\n")
        else:
            fd.write("		100 => array('class' => 'core:AttributeMap', 'name2oid'),\n")

        fd.write("	),\n")

        fd.write(");\n")
        if metadata:
            fd.write("$metadata[%s] = array_merge($metadata[%s], $further);" % (php_string(entityid), php_string(entityid)))

    fd.close()
    process = Popen(['/usr/bin/php', '-lf', filename], stderr=PIPE, stdout=PIPE,)
    stdout, stderr = process.communicate()
    if process.returncode:
        ud.debug(ud.LISTENER, ud.ERROR, 'broken PHP syntax(%d) in %s: %s%s' % (process.returncode, filename, stderr.decode('UTF-8', 'replace',), stdout.decode('UTF-8', 'replace',)),)
        try:
            with open(filename) as fd:
                ud.debug(ud.LISTENER, ud.ERROR, 'repr(%r)' % (fd.read(),),)
            os.unlink(filename)
        except IOError:
            pass
