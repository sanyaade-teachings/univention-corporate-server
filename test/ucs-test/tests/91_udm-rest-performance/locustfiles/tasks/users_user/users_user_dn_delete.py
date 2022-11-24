# Path: test/ucs-test/tests/91_udm-performance-test/locustfiles/tasks/locustfiles/tasks/users_user/users_user_dn_delete.py
# Remove a Users object
# Empty description
# # this file implements the Locust task for the following endpoints:
# # - DELETE /users/user/{dn}
#


def users_user_dn_delete(self):
    """DELETE /users/user/{dn}"""
    dn = 'string'  # The (urlencoded) LDAP Distinguished Name (DN).
    # query parameters for this endpoint
    query = {
        'cleanup': True,  # Whether to perform a cleanup (e.g. of temporary objects, locks, etc). (boolean)
        'recursive': True,  # Whether to remove referring objects (e.g. DNS or DHCP references). (boolean)
    }
    # header parameters for this endpoint
    header = {
        'User-Agent': '',  # The user agent. (string)
        'Accept-Language': '',  # The accepted response languages. (string)
        'If-None-Match': '',  # Use request from cache by using the E-Tag entity tag if it matches. (string)
        'If-Modified-Since': '',  # Use request from cache by using the Last-Modified date if it matches. (string)
        'X-Request-Id': '',  # A request-ID used for logging and tracing. (string)
    }
    self.request('delete', f'/univention/udm/users/user/{dn}', name='/users/user/{dn}', headers=header, params=query, verify=False, response_codes=[204])
