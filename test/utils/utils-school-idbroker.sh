#!/bin/bash
#
# Copyright 2022 Univention GmbH
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

set -x

ansible_register_idps_setup () {
	local traeger1_domain="${1:?missing traeger1_domain}"
	local traeger2_domain="${2:?missing traeger2_domain}"
	local repo_user="${3:?missing repo_user}"
	local repo_password_file="${4:?missing repo_password_file}"
	local rv=0
	wget -e robots=off --cut-dirs=3 -np -R "index.html*" --user "$repo_user" \
		--password="$(< "$repo_password_file")" -r -l 10 \
		"https://service.software-univention.de/apt/00342/docs/keycloak/" || rv=$?
	cd service.software-univention.de/keycloak || rv=$?
	printf "[keycloak]\nlocalhost\n" > hosts.ini
	openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -subj "/CN=id-broker" -keyout id-broker.key -out id-broker.cert
	curl -k "https://ucs-sso.$traeger1_domain/simplesamlphp/saml2/idp/metadata.php" > schools_saml_IDP/traeger1_metadata.xml
	curl -k "https://ucs-sso.$traeger2_domain/simplesamlphp/saml2/idp/metadata.php" > schools_saml_IDP/traeger2_metadata.xml
	printf "register_idps:\n  - alias: traeger1\n    ucsschoolSourceUID: IDBROKER-traeger1\n    path: schools_saml_IDP/traeger1_metadata.xml\n  - alias: traeger2\n    ucsschoolSourceUID: IDBROKER-traeger2\n    path: schools_saml_IDP/traeger2_metadata.xml\n" > schools_saml_IDP/idps.yml
	return $rv
}

# register IDBroker as service in ucs IdP
register_idbroker_as_sp_in_ucs () {
	local broker_fqdn="${1:?missing broker_fqdn}"
	local broker_ip="${2:?missing broker_ip}"
	local keycloak_identifier="${3:?missing keycloak_identifier=}"
	local rv=0
	ucr set hosts/static/"$broker_ip"="$broker_fqdn"
	udm saml/idpconfig modify \
		--dn "id=default-saml-idp,cn=univention,$(ucr get ldap/base)" \
		--append LdapGetAttributes=entryUUID
 	curl -k "https://$broker_fqdn/auth/realms/ID-Broker/broker/traeger1/endpoint/descriptor" > metadata.xml
	udm saml/serviceprovider create \
		--position "cn=saml-serviceprovider,cn=univention,$(ucr get ldap/base)" \
		--set serviceProviderMetadata="$(cat metadata.xml)" \
		--set AssertionConsumerService="https://$broker_fqdn/auth/realms/ID-Broker/broker/$keycloak_identifier/endpoint" \
		--set Identifier="https://$broker_fqdn/auth/realms/ID-Broker/broker/$keycloak_identifier/endpoint/descriptor" \
		--set isActivated=TRUE \
		--set simplesamlNameIDAttribute=entryUUID \
		--set simplesamlAttributes=TRUE \
		--set attributesNameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:uri" \
		--set LDAPattributes=entryUUID || rv=$?
	return $rv

}

add_bettermarks_app_portal_link () {
	local rv=0
	udm settings/portal_entry create \
		--position "cn=portal,cn=univention,$(ucr get ldap/base)" \
		--set activated=TRUE \
		--set authRestriction=anonymous \
		--set category=service \
		--set description="en_US \"bettermarks is an adaptive learning system for maths\"" \
		--set displayName="en_US \"bettermarks\"" \
		--set link="https://acc.bettermarks.com/auth/univention/DE_univention" \
		--set linkTarget=useportaldefault \
		--set name=univention-test-app \
		--set portal="cn=ucsschool_demo_portal,cn=portal,cn=univention,$(ucr get ldap/base)" \
		--set icon="$(base64 bettermarks-logo.svg)" || rv=$?
}

add_test_app_portal_link () {
	local broker_fqdn="${1:?missing broker_fqdn}"
	local keycloak_identifier="${2:?missing keycloak_identifier=}"
	local rv=0
	udm settings/portal_entry create \
		--position "cn=portal,cn=univention,$(ucr get ldap/base)" \
		--set activated=TRUE \
		--set authRestriction=anonymous \
		--set category=service \
		--set description="en_US \"Test app to check oauth login and tokens\"" \
		--set displayName="en_US \"Test oauth\"" \
		--set link="https://$broker_fqdn/univention-test-app?kc_idp_hint=$keycloak_identifier" \
		--set linkTarget=useportaldefault \
		--set name=univention-test-app \
		--set portal="cn=ucsschool_demo_portal,cn=portal,cn=univention,$(ucr get ldap/base)" \
		--set icon="$(base64 oidc-logo.svg)" || rv=$?
	return $rv
}

create_id_connector_school_authority_config () {
  local provisioning_fqdn="${1:?missing provisioning_fqdn}"
  local config_name="${2:?missing config_name}"
  local username="${3:?missing username}"
  local password="${4:?missing password}"

  token="$(curl -s -X POST https://$provisioning_fqdn/ucsschool/apis/auth/token \
    -H "Content-Type:application/x-www-form-urlencoded" \
    -d "username=$username" \
    -d "password=$password" \
    | python -c "import json, sys; print(json.loads(sys.stdin.read())['access_token'])" \
    )"
  curl -X POST "https://$provisioning_fqdn/ucsschool-id-connector/api/v1/school_authorities" \
    -H "accept: application/json" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"$config_name\",
      \"active\": true,
      \"url\": \"https://$provisioning_fqdn/\",
      \"plugins\": [\"id_broker-users\", \"id_broker-groups\"],
      \"plugin_configs\": {
          \"id_broker\": {
              \"password\": \"$password\",
              \"username\": \"$username\",
              \"version\": 1
          }
      }
  }"
}

create_school_users_classes () {
  local tr="${1:?missing traegernum}"
  local ou1="${tr}ou1"
  local ou2="${tr}ou2"

  /usr/share/ucs-school-import/scripts/create_ou "$ou1"
  /usr/share/ucs-school-import/scripts/create_ou "$ou2"
  i=1; python -m ucsschool.lib.models create --name "${tr}-stud${i}"  --set firstname "Traeger${i}" --set lastname "Student${i}" --set password univention --school DEMOSCHOOL Student
  i=1; python -m ucsschool.lib.models create --name "${tr}-teach${i}" --set firstname "Traeger${i}" --set lastname "Teacher${i}" --set password univention --school DEMOSCHOOL Teacher
  i=2; python -m ucsschool.lib.models create --name "${tr}-stud${i}"  --set firstname "Traeger${i}" --set lastname "Student${i}" --set password univention --school DEMOSCHOOL --append schools DEMOSCHOOL --append schools "$ou1" Student
  i=2; python -m ucsschool.lib.models create --name "${tr}-teach${i}" --set firstname "Traeger${i}" --set lastname "Teacher${i}" --set password univention --school DEMOSCHOOL --append schools DEMOSCHOOL --append schools "$ou1" Teacher
  i=3; python -m ucsschool.lib.models create --name "${tr}-stud${i}"  --set firstname "Traeger${i}" --set lastname "Student${i}" --set password univention --school "$ou1"     --append schools "$ou1"     --append schools "$ou2" Student
  i=3; python -m ucsschool.lib.models create --name "${tr}-teach${i}" --set firstname "Traeger${i}" --set lastname "Teacher${i}" --set password univention --school "$ou1"     --append schools "$ou1"     --append schools "$ou2" Teacher
  python -m ucsschool.lib.models modify --dn "cn=DEMOSCHOOL-Democlass,cn=klassen,cn=schueler,cn=groups,ou=DEMOSCHOOL,$(ucr get ldap/base)" \
    --append users "uid=${tr}-stud1,cn=schueler,cn=users,ou=DEMOSCHOOL,$(ucr get ldap/base)" \
    --append users "uid=${tr}-stud2,cn=schueler,cn=users,ou=DEMOSCHOOL,$(ucr get ldap/base)" \
    --append users "uid=${tr}-teach1,cn=lehrer,cn=users,ou=DEMOSCHOOL,$(ucr get ldap/base)" \
    --append users "uid=${tr}-teach2,cn=lehrer,cn=users,ou=DEMOSCHOOL,$(ucr get ldap/base)" SchoolClass
  python -m ucsschool.lib.models create SchoolClass \
    --name "${ou1}-1a" \
    --school "$ou1" \
    --append users "uid=${tr}-stud2,cn=schueler,cn=users,ou=DEMOSCHOOL,$(ucr get ldap/base)" \
    --append users "uid=${tr}-stud3,cn=schueler,cn=users,ou=${ou1},$(ucr get ldap/base)" \
    --append users "uid=${tr}-teach2,cn=lehrer,cn=users,ou=DEMOSCHOOL,$(ucr get ldap/base)" \
    --append users "uid=${tr}-teach3,cn=lehrer,cn=users,ou=${ou1},$(ucr get ldap/base)"
  python -m ucsschool.lib.models create SchoolClass \
    --name "${ou2}-1a" \
    --school "$ou2" \
    --append users "uid=${tr}-stud3,cn=schueler,cn=users,ou=${ou1},$(ucr get ldap/base)" \
    --append users "uid=${tr}-teach3,cn=lehrer,cn=users,ou=${ou1},$(ucr get ldap/base)"
}

# vim:set filetype=sh ts=4:
