#!/usr/share/ucs-test/runner python3
## desc: Test the UMC backend process killing
## bugs: [34593, 38174]
## exposure: dangerous

import signal
import sys
from os import WNOHANG, WTERMSIG, fork, wait4
from time import sleep

from psutil import Process, TimeoutExpired

import univention.testing.utils as utils

from umc import UMCBase


class TestUMCProcessKilling(UMCBase):
    MAX_PROCESS_TIME = 30  # seconds

    def __init__(self):
        """Test Class constructor"""
        super(TestUMCProcessKilling, self).__init__()
        self.proc = None

    def make_kill_request(self, signal, pids):
        """
        Applies the kill action with a signal 'signal' to the list of 'pids'
        provided by making a UMC request 'top/kill' with respective options.
        """
        self.client.umc_command('top/kill', {'signal': signal, 'pid': pids})

    def query_process_exists(self, pid):
        """
        Checks if process with a provided 'pid' exists
        by making the UMC request 'top/query'.
        Returns True when exists.
        """
        return any(result['pid'] == pid and sys.executable in result['command'] for result in self.client.umc_command('top/query').result)

    def force_process_kill(self):
        """
        Kills process with SIGKILL signal via psutil if not yet terminated.
        That is a clean-up action.
        """
        if self.proc and self.proc.is_running():
            print("Created process with pid '%s' was not terminated, "
                  "forcing kill using psutil" % self.proc.pid)
            self.proc.kill()

            try:
                # wait a bit for process to be killed
                self.proc.wait(timeout=5)
            except TimeoutExpired as exc:
                print("Process with pid '%s' did not exit after forced KILL "
                      "via psutil: %r" % (self.proc.pid, exc))

    def create_process(self, ignore_sigterm=False):
        """
        Initiates a simple test process that should be killed after by forking.
        Creates a psutil Process class to check running state
        before terminating. Also returns process id (pid).
        """
        pid = fork()
        if pid:  # parent
            self.proc = Process(pid)
            return pid
        else:  # child under test
            if ignore_sigterm:
                # the process should ignore 'SIGTERM'
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
            sleep(self.MAX_PROCESS_TIME)
            sys.exit(0)

    def test(self, signame, ignore_signal=False):
        """
        Creates a process;
        Check created process exist via UMC;
        Kills/Terminates process with a given 'signame' via UMC;
        Performs clean-up using psutil if needed.
        """
        print("\nTesting UMC process killing with signal '%s'" % signame)
        signum = getattr(signal, signame)
        try:
            pid = self.create_process(ignore_signal)
            if self.query_process_exists(pid):  # a UMC request
                self.make_kill_request(signame, [pid])  # a UMC request

                for i in range(self.MAX_PROCESS_TIME):
                    if i:
                        sleep(1)
                    child, exit_status, _res_usage = wait4(pid, WNOHANG)
                    if child:
                        break

                print("Process Exit Status is: ", exit_status)
                exit_code = WTERMSIG(exit_status)

                if ignore_signal:
                    # case 3:
                    if exit_code in (signum, getattr(signal, 'SIGKILL')):
                        # process exited due to given signal or SIGKILL, i.e.
                        # the UMC forced the kill of unwilling process:
                        utils.fail("The exit code of unwilling process is %s."
                                   " The process was terminated either with "
                                   "SIGKILL or SIGTERM." % exit_code)
                else:
                    # cases 1 and 2:
                    if exit_code != signum:
                        utils.fail("Process exit status is 0x%x instead of "
                                   "%s(%d)." % (exit_status, signame, signum))
                    if self.query_process_exists(pid):  # a UMC request
                        utils.fail("Process did not terminate after request "
                                   "with signal %s" % signame)
            else:
                utils.fail("The process is not running right after creation")
        finally:
            self.force_process_kill()

    def main(self):
        """
        Method to start the test of the UMC backend process killing.
        """
        self.create_connection_authenticate()
        print("Test process max running time (sec) is:", self.MAX_PROCESS_TIME)

        # case 1: killing process using signal 'SIGTERM'
        self.test('SIGTERM')

        # case 2: killing process using signal 'SIGKILL'
        self.test('SIGKILL')

        # case 3: try to kill a process with 'SIGTERM' when
        # the process ignores 'SIGTERM'. To make sure that UMC won't
        # force kill (with SIGKILL) such unwilling process.
        self.test('SIGTERM', ignore_signal=True)


if __name__ == '__main__':
    TestUMC = TestUMCProcessKilling()
    sys.exit(TestUMC.main())
