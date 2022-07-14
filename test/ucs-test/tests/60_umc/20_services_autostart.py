#!/usr/share/ucs-test/runner python3
## desc: Test the UMC service module autostart behavior
## bugs: [34506]
## exposure: dangerous

import sys

import univention.testing.utils as utils
from univention.config_registry.frontend import ucr_update

from umc import ServiceModule


class TestUMCServiceAutostart(ServiceModule):

    def __init__(self):
        """Test Class constructor"""
        super(TestUMCServiceAutostart, self).__init__()
        self.initial_service_config = None

    def restore_initial_configuration(self, service_name):
        """
        Restores the autostart configuration as saved in the global var
        for provided 'service_name'
        """
        ucr_update(self.ucr,
                   {service_name + '/autostart': self.initial_service_config})

    def get_service_current_configuration(self, service_name_value):
        """
        Get the current UCR configuration for provided 'service_name_value' var
        Reloads the UCR before proceeding.
        """
        self.ucr.load()
        return self.ucr.get(service_name_value)

    def set_service_configuration(self, service_names, setting):
        """Set the 'setting' for list of 'service_names' via UMC request"""
        try:
            request_result = self.client.umc_command('services/' + setting, service_names).result
            if not request_result:
                utils.fail("Request 'services/%s' failed, no response "
                           "from hostname '%s'" % (setting, self.hostname))
            if not request_result['success']:
                utils.fail("Request 'services/%s' failed, no success in "
                           "response. Hostname '%s', response '%s'" %
                           (setting, self.hostname, request_result))
        except Exception as exc:
            utils.fail("Exception while making services/%s request: %s" %
                       (setting, exc))

    def check_service_autostart_possibilities(self, service_name):
        """
        Check all the possible variations of 'service_name' autostart settings
        """
        autostart_var = service_name + '/autostart'

        # saving initial service configuration
        self.initial_service_config = self.get_service_current_configuration(
            autostart_var)

        # make sure that 'service_name' autostart == 'yes' at first
        if self.get_service_current_configuration(autostart_var) != 'yes':
            self.set_service_configuration([service_name], 'start_auto')
            if self.get_service_current_configuration(autostart_var) != 'yes':
                utils.fail("Failed to set initial '%s' setting to "
                           "'yes'" % autostart_var)

        # case 1: autostart == 'yes', changing to 'no'
        if self.get_service_current_configuration(autostart_var) == 'yes':
            self.set_service_configuration([service_name], 'start_never')
            if self.get_service_current_configuration(autostart_var) != 'no':
                utils.fail("The '%s' was not changed from "
                           "'yes' to 'no' in UCR" % autostart_var)

        # case 2: autostart == 'no', changing to 'manually'
        if self.get_service_current_configuration(autostart_var) == 'no':
            self.set_service_configuration([service_name], 'start_manual')
            if self.get_service_current_configuration(autostart_var) != 'manually':
                utils.fail("The '%s' was not changed from "
                           "'no' to 'manually' in UCR" % autostart_var)

        # case 3: autostart == 'manually', changing to 'no'
        if self.get_service_current_configuration(autostart_var) == 'manually':
            self.set_service_configuration([service_name], 'start_never')
            if self.get_service_current_configuration(autostart_var) != 'no':
                utils.fail("The '%s' was not changed from "
                           "'manually' to 'no' in UCR" % autostart_var)

        # case 4: autostart == 'no', changing to 'yes'
        if self.get_service_current_configuration(autostart_var) == 'no':
            self.set_service_configuration([service_name], 'start_auto')
            if self.get_service_current_configuration(autostart_var) != 'yes':
                utils.fail("The '%s' was not changed from "
                           "'no' to 'yes' in UCR" % autostart_var)

        # case 5: autostart == 'yes', changing to 'manually'
        if self.get_service_current_configuration(autostart_var) == 'yes':
            self.set_service_configuration([service_name], 'start_manual')
            if self.get_service_current_configuration(autostart_var) != 'manually':
                utils.fail("The '%s' was not changed from "
                           "'yes' to 'manually' in UCR" % autostart_var)

        # case 6: autostart == 'manually', changing to 'yes'
        if self.get_service_current_configuration(autostart_var) == 'manually':
            self.set_service_configuration([service_name], 'start_auto')
            if self.get_service_current_configuration(autostart_var) != 'yes':
                utils.fail("The '%s' was not changed from "
                           "'manually' to 'yes' in UCR" % autostart_var)

    def main(self, service_name):
        """
        Method to test the UMC 'service_name' service
        autostart behavior
        """
        self.create_connection_authenticate()

        self.check_service_presence(self.query(), service_name)
        try:
            self.check_service_autostart_possibilities(service_name)
        finally:
            self.restore_initial_configuration(service_name)


if __name__ == '__main__':
    TestUMC = TestUMCServiceAutostart()
    sys.exit(TestUMC.main('nscd'))  # tesing 'Name Service Caching Daemon'
