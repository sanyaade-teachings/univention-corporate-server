#!/usr/bin/python3

from univention.config_registry import ucr


O365CLIENT = {'id': '13cda498-e3f9-4c27-bedb-768c2839a0ca', 'clientId': 'urn:federation:MicrosoftOnline', 'surrogateAuthRequired': False, 'enabled': True, 'alwaysDisplayInConsole': False, 'clientAuthenticatorType': 'client-secret', 'redirectUris': ['https://login.microsoftonline.com/login.srf'], 'webOrigins': [], 'notBefore': 0, 'bearerOnly': False, 'consentRequired': False, 'standardFlowEnabled': True, 'implicitFlowEnabled': False, 'directAccessGrantsEnabled': True, 'serviceAccountsEnabled': False, 'publicClient': True, 'frontchannelLogout': True, 'protocol': 'saml', 'attributes': {'saml.multivalued.roles': 'false', 'saml.force.post.binding': 'true', 'post.logout.redirect.uris': '+', 'oauth2.device.authorization.grant.enabled': 'false', 'backchannel.logout.revoke.offline.tokens': 'false', 'saml.server.signature.keyinfo.ext': 'false', 'use.refresh.tokens': 'true', 'oidc.ciba.grant.enabled': 'false', 'backchannel.logout.session.required': 'true', 'client_credentials.use_refresh_token': 'false', 'saml.signature.algorithm': 'RSA_SHA256', 'saml.client.signature': 'false', 'require.pushed.authorization.requests': 'false', 'saml.allow.ecp.flow': 'false', 'id.token.as.detached.signature': 'false', 'saml.assertion.signature': 'true', 'saml_single_logout_service_url_post': 'https://login.microsoftonline.com/login.srf', 'saml.encrypt': 'false', 'saml_assertion_consumer_url_post': 'https://login.microsoftonline.com/login.srf', 'saml.server.signature': 'true', 'saml_idp_initiated_sso_url_name': 'MicrosoftOnline', 'exclude.session.state.from.auth.response': 'false', 'saml.artifact.binding.identifier': 'Ohzdm/95RuxvhGbq/vi8GUTaHf4=', 'saml.artifact.binding': 'false', 'saml_force_name_id_format': 'true', 'tls.client.certificate.bound.access.tokens': 'false', 'acr.loa.map': '{}', 'saml.authnstatement': 'true', 'display.on.consent.screen': 'false', 'saml.assertion.lifespan': '300', 'saml_name_id_format': 'persistent', 'token.response.type.bearer.lower-case': 'false', 'saml.onetimeuse.condition': 'false', 'saml_signature_canonicalization_method': 'http://www.w3.org/2001/10/xml-exc-c14n#'}, 'authenticationFlowBindingOverrides': {}, 'fullScopeAllowed': True, 'nodeReRegistrationTimeout': -1, 'defaultClientScopes': [], 'optionalClientScopes': [], 'access': {'view': True, 'configure': True, 'manage': True}}


GOOGLE_CLIENT = {'id': 'dc72d8ae-7f4b-447c-87b3-1446c8d31e87', 'clientId': 'google.com', 'surrogateAuthRequired': False, 'enabled': True, 'alwaysDisplayInConsole': False, 'clientAuthenticatorType': 'client-secret', 'redirectUris': [], 'webOrigins': [], 'notBefore': 0, 'bearerOnly': False, 'consentRequired': False, 'standardFlowEnabled': True, 'implicitFlowEnabled': False, 'directAccessGrantsEnabled': True, 'serviceAccountsEnabled': False, 'publicClient': True, 'frontchannelLogout': False, 'protocol': 'saml', 'attributes': {'saml.multivalued.roles': 'false', 'saml.force.post.binding': 'true', 'oauth2.device.authorization.grant.enabled': 'false', 'backchannel.logout.revoke.offline.tokens': 'false', 'saml.server.signature.keyinfo.ext': 'false', 'use.refresh.tokens': 'true', 'oidc.ciba.grant.enabled': 'false', 'backchannel.logout.session.required': 'true', 'client_credentials.use_refresh_token': 'false', 'saml.signature.algorithm': 'RSA_SHA256', 'saml.client.signature': 'false', 'require.pushed.authorization.requests': 'false', 'saml.allow.ecp.flow': 'false', 'id.token.as.detached.signature': 'false', 'saml.assertion.signature': 'true', 'saml_single_logout_service_url_post': 'https://www.google.com/a/testdomain.com/acs', 'saml.encrypt': 'false', 'saml_assertion_consumer_url_post': 'https://www.google.com/a/testdomain.com/acs', 'saml.server.signature': 'true', 'saml_idp_initiated_sso_url_name': 'google.com', 'exclude.session.state.from.auth.response': 'false', 'saml.artifact.binding.identifier': 'uuqVS5VzHGiubkW9HiUutFYM3EU=', 'saml.artifact.binding': 'false', 'saml_force_name_id_format': 'false', 'tls.client.certificate.bound.access.tokens': 'false', 'acr.loa.map': '{}', 'saml.authnstatement': 'true', 'display.on.consent.screen': 'false', 'saml.assertion.lifespan': '300', 'saml_name_id_format': 'email', 'token.response.type.bearer.lower-case': 'false', 'saml.onetimeuse.condition': 'false', 'saml_signature_canonicalization_method': 'http://www.w3.org/2001/10/xml-exc-c14n#'}, 'authenticationFlowBindingOverrides': {}, 'fullScopeAllowed': True, 'nodeReRegistrationTimeout': -1, 'protocolMappers': [{'id': '53bce0b9-d2f3-4147-9ee6-c3b82e9483cd', 'name': 'userid_mapper', 'protocol': 'saml', 'protocolMapper': 'saml-user-attribute-mapper', 'consentRequired': False, 'config': {'attribute.nameformat': 'Basic', 'user.attribute': 'uid', 'friendly.name': 'uid', 'attribute.name': 'uid'}}], 'defaultClientScopes': [], 'optionalClientScopes': [], 'access': {'view': True, 'configure': True, 'manage': True}}

NC_CLIENT = {'id': 'e19d6f3c-33b9-45e9-9306-b43e6b4da9f9', 'clientId': 'https://backup.ucs.test/nextcloud/apps/user_saml/saml/metadata', 'surrogateAuthRequired': False, 'enabled': True, 'alwaysDisplayInConsole': False, 'clientAuthenticatorType': 'client-secret', 'redirectUris': ['https://backup.ucs.test/nextcloud/apps/user_saml/saml/sls', 'https://backup.ucs.test/nextcloud/apps/user_saml/saml/acs'], 'webOrigins': [], 'notBefore': 0, 'bearerOnly': False, 'consentRequired': False, 'standardFlowEnabled': True, 'implicitFlowEnabled': False, 'directAccessGrantsEnabled': True, 'serviceAccountsEnabled': False, 'publicClient': True, 'frontchannelLogout': True, 'protocol': 'saml', 'attributes': {'saml.multivalued.roles': 'false', 'saml.force.post.binding': 'true', 'post.logout.redirect.uris': '+', 'oauth2.device.authorization.grant.enabled': 'false', 'backchannel.logout.revoke.offline.tokens': 'false', 'saml.server.signature.keyinfo.ext': 'false', 'use.refresh.tokens': 'true', 'oidc.ciba.grant.enabled': 'false', 'backchannel.logout.session.required': 'true', 'client_credentials.use_refresh_token': 'false', 'saml.signature.algorithm': 'RSA_SHA256', 'saml.client.signature': 'false', 'require.pushed.authorization.requests': 'false', 'saml.allow.ecp.flow': 'false', 'id.token.as.detached.signature': 'false', 'saml.assertion.signature': 'true', 'saml.encrypt': 'false', 'saml_assertion_consumer_url_post': 'https://backup.ucs.test/nextcloud/apps/user_saml/saml/acs', 'saml.server.signature': 'true', 'exclude.session.state.from.auth.response': 'false', 'saml.artifact.binding.identifier': 'o9mvrwCJYjX2qtSjYoQTxiLHVog=', 'saml.artifact.binding': 'false', 'saml_single_logout_service_url_redirect': 'https://backup.ucs.test/nextcloud/apps/user_saml/saml/sls', 'saml_force_name_id_format': 'true', 'tls.client.certificate.bound.access.tokens': 'false', 'acr.loa.map': '{}', 'saml.authnstatement': 'true', 'display.on.consent.screen': 'false', 'saml.assertion.lifespan': '300', 'saml_name_id_format': 'username', 'token.response.type.bearer.lower-case': 'false', 'saml.onetimeuse.condition': 'false', 'saml_signature_canonicalization_method': 'http://www.w3.org/2001/10/xml-exc-c14n#'}, 'authenticationFlowBindingOverrides': {}, 'fullScopeAllowed': True, 'nodeReRegistrationTimeout': -1, 'defaultClientScopes': [], 'optionalClientScopes': [], 'access': {'view': True, 'configure': True, 'manage': True}}


OC_CLIENT = {'id': 'c93a7dd3-78e7-4563-8339-00282957db4d', 'clientId': 'owncloudclient', 'name': 'owncloudclient', 'description': '', 'rootUrl': 'https://backup.ucs.test/owncloud/apps/openidconnect/redirect', 'adminUrl': '', 'baseUrl': 'https://backup.ucs.test/owncloud/apps/openidconnect/redirect', 'surrogateAuthRequired': False, 'enabled': True, 'alwaysDisplayInConsole': False, 'clientAuthenticatorType': 'client-secret', 'secret': 'univention', 'redirectUris': ['https://backup.ucs.test/owncloud/apps/openidconnect/redirect', f'https://{ucr.get("hostname")}.{ucr.get("domainname")}'], 'webOrigins': ['https://backup.ucs.test/owncloud/apps/openidconnect/redirect', f'https://{ucr.get("hostname")}.{ucr.get("domainname")}'], 'notBefore': 0, 'bearerOnly': False, 'consentRequired': False, 'standardFlowEnabled': True, 'implicitFlowEnabled': False, 'directAccessGrantsEnabled': False, 'serviceAccountsEnabled': False, 'publicClient': False, 'frontchannelLogout': False, 'protocol': 'openid-connect', 'attributes': {'saml.multivalued.roles': 'false', 'saml.force.post.binding': 'false', 'frontchannel.logout.session.required': 'false', 'oauth2.device.authorization.grant.enabled': 'false', 'backchannel.logout.revoke.offline.tokens': 'false', 'saml.server.signature.keyinfo.ext': 'false', 'use.refresh.tokens': 'true', 'oidc.ciba.grant.enabled': 'false', 'backchannel.logout.session.required': 'true', 'client_credentials.use_refresh_token': 'false', 'saml.client.signature': 'false', 'require.pushed.authorization.requests': 'false', 'saml.allow.ecp.flow': 'false', 'saml.assertion.signature': 'false', 'id.token.as.detached.signature': 'false', 'client.secret.creation.time': '1661514856', 'saml.encrypt': 'false', 'saml.server.signature': 'false', 'exclude.session.state.from.auth.response': 'false', 'saml.artifact.binding': 'false', 'saml_force_name_id_format': 'false', 'tls.client.certificate.bound.access.tokens': 'false', 'acr.loa.map': '{}', 'saml.authnstatement': 'false', 'display.on.consent.screen': 'false', 'token.response.type.bearer.lower-case': 'false', 'saml.onetimeuse.condition': 'false'}, 'authenticationFlowBindingOverrides': {}, 'fullScopeAllowed': True, 'nodeReRegistrationTimeout': -1, 'protocolMappers': [{'name': 'email', 'protocol': 'openid-connect', 'protocolMapper': 'oidc-usermodel-property-mapper', 'consentRequired': False, 'config': {'userinfo.token.claim': 'true', 'user.attribute': 'email', 'id.token.claim': 'true', 'access.token.claim': 'true', 'claim.name': 'email', 'jsonType.label': 'String'}}, {'name': 'username', 'protocol': 'openid-connect', 'protocolMapper': 'oidc-usermodel-property-mapper', 'consentRequired': False, 'config': {'userinfo.token.claim': 'true', 'user.attribute': 'username', 'id.token.claim': 'true', 'access.token.claim': 'true', 'claim.name': 'preferred_username', 'jsonType.label': 'String'}}, {'name': 'uid', 'protocol': 'openid-connect', 'protocolMapper': 'oidc-usermodel-attribute-mapper', 'consentRequired': False, 'config': {'userinfo.token.claim': 'true', 'user.attribute': 'uid', 'id.token.claim': 'true', 'access.token.claim': 'true', 'claim.name': 'uid', 'jsonType.label': 'String'}}], 'defaultClientScopes': ['web-origins', 'acr', 'roles', 'profile', 'email'], 'optionalClientScopes': ['address', 'phone', 'offline_access', 'microprofile-jwt'], 'access': {'view': True, 'configure': True, 'manage': True}}
