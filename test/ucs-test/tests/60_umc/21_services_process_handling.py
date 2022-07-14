#!/usr/share/ucs-test/runner python3
## desc: Test the UMC service module process handling
## bugs: [34505]
## exposure: dangerous

import subprocess
import sys

import univention.testing.utils as utils

from umc import ServiceModule


class TestUMCServiceProcessHandling(ServiceModule):

    def __init__(self, service_name):
        """Test Class constructor"""
        super(TestUMCServiceProcessHandling, self).__init__()
        self.service_name = service_name
        self.initial_service_state_running = None

    def restore_initial_state(self):
        """
        Restores the initial 'service_name' state as saved in the global var
        'initial_service_state_running' using 'do_service_action' method.
        """
        if self.initial_service_state_running:
            print("Trying to restore the '%s' service to initially "
                  "running state" % self.service_name)
            self.do_service_action([self.service_name], 'start')
            if not self.query_service_is_running():
                utils.fail("Failed to restore '%s' to initial running state"
                           % self.service_name)
            if not self.get_service_current_pid():
                utils.fail("Failed to restore '%s' to initial running state,"
                           " the process id is empty." % self.service_name)
        elif self.initial_service_state_running is False:
            print("Trying to restore the '%s' to initially stopped state"
                  % self.service_name)
            self.do_service_action([self.service_name], 'stop')
            if self.query_service_is_running():
                utils.fail("Failed to restore %s' to initial stopped state"
                           % self.service_name)
            if self.get_service_current_pid():
                utils.fail("Failed to restore '%s' to initial stopped state,"
                           " the process id is not empty." % self.service_name)

    def query_service_is_running(self):
        """
        Get the current state for provided 'service_name' by making
        'services/query' UMC request and returning 'isRunning' field value
        """
        request_result = self.query()
        for result in request_result:
            try:
                if result['service'] == self.service_name:
                    return result['isRunning']
            except KeyError as exc:
                utils.fail("Couldn't find the '%s' field for "
                           "service: %s" % (exc, self.service_name))
        else:
            utils.fail("Couldn't find service %s: %s" % (
                self.service_name, request_result))

    def get_service_current_pid(self):
        """
        Get the process id for the provided 'service_name' by using pgrep.
        Returns pid as a string.
        """
        proc = subprocess.Popen(("pgrep", self.service_name),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        try:
            stdout, stderr = proc.communicate()
            if not stderr:
                return stdout.rstrip()
            else:
                utils.fail("Error occurred while pgrep'ing the '%s' service:"
                           " '%s'" % (self.service_name, stderr))
        except OSError as exc:
            utils.fail("Error occurred while getting output from process "
                       " pgrep'ing '%s': '%s' " % (self.service_name, exc))

    def do_service_action(self, service_names, action):
        """
        Applies an 'action' for provided 'service_names' list via UMC request.
        Possible options for actions are: start/stop/restart.
        """
        try:
            request_result = self.client.umc_command('services/' + action, service_names).result
            if not request_result:
                utils.fail("Request 'services/%s' failed, no response "
                           "from hostname '%s'" % (action, self.hostname))
            if not request_result['success']:
                utils.fail("Request 'services/%s' failed, no success in "
                           "response. Hostname '%s', response '%s'" %
                           (action, self.hostname, request_result))
        except Exception as exc:
            utils.fail("Exception while making services/%s request: %s" %
                       (action, exc))

    def save_initial_service_state(self):
        """
        Saves the initial state of the process (Running == True ;
        Stopped == False).
        Makes a check if pid is not empty when process is running
        and v.v. - that pid is empty when 'service_name' is stopped.
        """
        self.initial_service_state_running = self.query_service_is_running()

        if self.initial_service_state_running:
            if not self.get_service_current_pid():
                utils.fail("The '%s' was initially shown as running, but "
                           "process id is empty." % self.service_name)
        else:
            if self.get_service_current_pid():
                utils.fail("The '%s' was initially shown as stopped, "
                           "but process id is not empty." % self.service_name)

    def check_service_process_states(self):
        """
        Check all the possible variations of 'service_name' process state.
        Saves initial state before proceeding.
        """
        self.save_initial_service_state()

        print("Stopping the '%s' service first to cover all the test cases" % self.service_name)
        self.do_service_action([self.service_name], 'stop')
        if self.query_service_is_running():
            utils.fail("Could not make '%s' service stop, UMC services/queryrequest shows it as running" % self.service_name)
        if self.get_service_current_pid():
            utils.fail("The '%s' service pid is not empty after stopping"
                       % self.service_name)

        print("Test case 1: trying to start the not running '%s' service" % self.service_name)
        self.do_service_action([self.service_name], 'start')
        if not self.query_service_is_running():
            utils.fail("Could not make '%s' service start, UMC services/query request shows it as not running" % self.service_name)

        last_service_pid = self.get_service_current_pid()
        if not last_service_pid:
            utils.fail("The '%s' service pid is empty after starting" % self.service_name)

        print("Test case 2: trying to restart already running '%s' service" % self.service_name)
        self.do_service_action([self.service_name], 'restart')
        if not self.query_service_is_running():
            utils.fail("Could not make '%s' service restart, UMC services/query request shows it as not running" % self.service_name)

        current_service_pid = self.get_service_current_pid()
        if not current_service_pid:
            utils.fail("The '%s' service pid is empty after restarting" % self.service_name)
        if current_service_pid == last_service_pid:
            utils.fail("The '%s' service process id did not change after restarting" % self.service_name)

        print("Test case 3: trying to stop the running '%s' service" % self.service_name)
        self.do_service_action([self.service_name], 'stop')
        if self.query_service_is_running():
            utils.fail("Could not make '%s' service stop, UMC services/query request shows it as running" % self.service_name)
        if self.get_service_current_pid():
            utils.fail("The '%s' service pid is not empty after stopping" % self.service_name)

        print("Test case 4: trying to restart the not running '%s' service" % self.service_name)
        self.do_service_action([self.service_name], 'restart')
        if not self.query_service_is_running():
            utils.fail("Could not make '%s' service start (via restart), UMC services/query request shows it as not running" % self.service_name)

        last_service_pid = self.get_service_current_pid()
        if not last_service_pid:
            utils.fail("The '%s' service pid is empty after starting (via restart)" % self.service_name)

        print("Test case 5: trying to start already running '%s' service" % self.service_name)
        self.do_service_action([self.service_name], 'start')
        if not self.query_service_is_running():
            utils.fail("Could not make '%s' service start, UMC services/query request shows it as not running" % self.service_name)
        current_service_pid = self.get_service_current_pid()
        if not current_service_pid:
            utils.fail("The '%s' service pid is empty after starting" % self.service_name)
        if current_service_pid != last_service_pid:
            utils.fail("The '%s' service process id changed while process should not have been restarted" % self.service_name)

        print("Test case 6: trying to stop the running '%s' service" % self.service_name)
        self.do_service_action([self.service_name], 'stop')
        if self.query_service_is_running():
            utils.fail("Could not make '%s' service stop, UMC services/query request shows it as running" % self.service_name)
        if self.get_service_current_pid():
            utils.fail("The '%s' service pid is not empty after stopping" % self.service_name)

    def main(self):
        """
        Method to test the UMC globally defined 'service_name' service process
        start/stop/restart behavior.
        """
        self.create_connection_authenticate()

        initial_state = self.query()
        self.check_service_presence(initial_state, self.service_name)
        for result in initial_state:
            try:
                if result['service'] == self.service_name:
                    if result['autostart'] in ('no', 'false'):
                        print("Skipped due to: %s/autostart=%s" % (self.service_name, result['autostart']))
                        self.return_code_result_skip()
            except KeyError as exc:
                utils.fail("KeyError '%s' while looking for 'service' or 'autostart' in services query results" % exc)
        try:
            self.check_service_process_states()
        finally:
            self.restore_initial_state()


if __name__ == '__main__':
    TestUMC = TestUMCServiceProcessHandling('nscd')
    sys.exit(TestUMC.main())
