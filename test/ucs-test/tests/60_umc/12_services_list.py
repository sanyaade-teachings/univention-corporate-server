#!/usr/share/ucs-test/runner python3
## desc: Test the output of the UMC service module
## bugs: [34445]
## exposure: safe

import sys

import univention.testing.utils as utils
from univention.testing.codes import TestCodes

from umc import ServiceModule


class TestUMCServiceList(ServiceModule):

    def check_response_structure(self, request_result):
        """Check the response general structure for obligatory keys"""
        for result in request_result:
            if 'service' not in result:
                utils.fail("The 'service' field was not found in the "
                           "UMC response: %s" % result)
            if 'isRunning' not in result:
                utils.fail("The 'isRunning' field was not found in the "
                           "UMC response: %s" % result)
            if 'description' not in result:
                utils.fail("The 'description' field was not found in the "
                           "UMC response: %s" % result)
            if 'autostart' not in result:
                utils.fail("The 'autostart' field was not found in the "
                           "UMC response: %s" % result)

    def check_directory_listener(self, request_result):
        """
        Check if the 'Univention Directory Listener' was listed in the response
        """
        for result in request_result:
            if result['service'] == 'univention-directory-listener':
                break
        else:
            utils.fail("The 'Univention Directory Listener' service was not "
                       "found in the UMC response: %s" % request_result)

    def return_code_result_skip(self):
        """Method to stop the test with the code 77, RESULT_SKIP """
        sys.exit(TestCodes.RESULT_SKIP)

    def main(self):
        """Method to start the test of UMC services listing"""
        self.create_connection_authenticate()
        request_result = self.query()
        self.check_response_structure(request_result)
        self.check_directory_listener(request_result)


if __name__ == '__main__':
    TestUMC = TestUMCServiceList()
    sys.exit(TestUMC.main())
