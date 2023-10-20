#!/usr/share/ucs-test/runner python3
## desc: Test the reconnect mechanism of univention-ldapsearch
## tags: [apptest,reconnect]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave]
## packages: [python3-psutil]
## bugs: [34293, 37299]
## exposure: dangerous
## versions:
##  4.0-0: skip
##  4.0-1: fixed

from multiprocessing import Process
from queue import Empty, Full
from subprocess import PIPE, Popen
from time import sleep

import psutil

from univention.config_registry import ConfigRegistry, handler_set
from univention.testing.codes import TestCodes
from univention.testing.utils import fail


UCR = ConfigRegistry()
UCR.load()


def restore_retry_count():
    """Sets UCR 'ldap/client/retry/count' to 'ucr_retry_count'."""
    stop_slapd()
    print("Restoring initial UCR 'ldap/client/retry/count' to", ucr_retry_count)
    set_ucr_retry_count(ucr_retry_count)
    start_slapd()


def set_ucr_retry_count(count):
    """Sets the 'ldap/client/retry/count' in the UCR."""
    ucr_var = f"ldap/client/retry/count={count}"
    handler_set((ucr_var,))


def univention_ldapsearch(fail_on_success):
    """A wrapper for 'univention-ldapsearch'"""
    proc = Popen(('univention-ldapsearch', '-s', 'base', 'dn', '-LLL'), stdout=PIPE, stderr=PIPE, shell=False)

    stdout, stderr = proc.communicate()
    stderr = stderr.decode('UTF-8')
    stdout = stdout.decode('UTF-8')
    if stderr:
        print("\nunivention-ldapsearch STDERR:\n", stderr.strip())
    if stdout:
        print("\nunivention-ldapsearch STDOUT:\n", stdout.strip())

    if ((base_dn in stdout) and fail_on_success):
        fail("\nThe 'univention-ldapsearch' worked when it is "
             "not expected to work.\n")

    if ((base_dn not in stdout) and not fail_on_success):
        fail("\nThe 'univention-ldapsearch' did not work in case it "
             "is expected to work.\n")


def perform_univention_ldapsearch(fail_on_success=False):
    """
    Runs univention-ldapsearch in a separate process with a timeout to
    avoid deadlocks. Checks the exit code of the process with
    'univention-ldapsearch'.
    """
    print("\nPerforming 'univention-ldapsearch -s base dn -LLL'")
    try:
        # start a separate process with timeout
        Proc = Process(target=univention_ldapsearch, args=(fail_on_success,))
        Proc.start()
        Proc.join(60)  # timeout = 60 seconds

        if Proc.exitcode != TestCodes.RESULT_OKAY:
            fail("The univention-ldapsearch did not return correct code. "
                 "Please check the complete output.")

    except (Empty, Full) as exc:
        fail("An '%r' Error occurred while performing 'univention-ldapsearch'. "
             "Probably 'univention-ldapsearch' did not work in 60 seconds "
             "timeout." % exc)


def stop_slapd():
    """
    Stops the slapd and waits for it to be stopped.
    Looks for slapd in processes and waits if found extra 15 seconds.
    """
    ret_code = Popen(('invoke-rc.d', 'slapd', 'stop')).wait()
    if ret_code != 0:
        fail(f"Expecting the return code to be 0, while it is: {ret_code}")

    # look for process and wait up to 15 seconds for its termination:
    for proc in psutil.process_iter():
        try:
            if 'slapd' in proc.name() and proc.ppid() == 1:
                print("\nThe 'slapd' is still running, waiting...")
                try:
                    proc.wait(15)
                    print("slapd terminated.")
                except psutil.TimeoutExpired:
                    fail("\nFailed to wait for slapd to terminate.\n")
        except psutil.NoSuchProcess:
            pass


def start_slapd():
    """Starts the slapd and wait for it to be started."""
    ret_code = Popen(('invoke-rc.d', 'slapd', 'start')).wait()
    if ret_code not in (0, 2):
        fail(f"Expecting the return code to be 0 or 2, while it is: {ret_code}")


def start_with_delay(delay):
    """Sleeps the given 'delay' and starts slapd."""
    Popen(f'sleep {delay}; invoke-rc.d slapd start', shell=True)


def wait_for_slapd_to_be_started():
    """Looks for slapd process and sleeos few seconds if not found."""
    for proc in psutil.process_iter():
        if 'slapd' in proc.name() and proc.ppid() == 1:
            # 'slapd' process found
            return

    # if not found, wait few more seconds
    sleep(5)


def print_test_header(header):
    print('\n**********************************************************************************')
    print(header)
    print('**********************************************************************************')


def main():
    try:
        set_ucr_retry_count(10)
        print_test_header("Case 1: Stop and start slapd with 5 secs "
                          "delay. Perform search. Retry count is 10.")
        stop_slapd()
        start_with_delay(5)
        perform_univention_ldapsearch()
        wait_for_slapd_to_be_started()

        set_ucr_retry_count(1)
        print_test_header("Case 2: Stop and start slapd with 5 secs "
                          "delay. Perform search. Retry count is 1.")
        print("Expecting that search case won't work, as retry count is 1 and start delay is 5.")
        stop_slapd()
        start_with_delay(5)
        perform_univention_ldapsearch(True)  # fail on success
        wait_for_slapd_to_be_started()

        set_ucr_retry_count(11)
        print_test_header("Case 3: Stop and start slapd with 7 secs "
                          "delay. Perform search. Retry count is 11.")
        stop_slapd()
        start_with_delay(7)
        perform_univention_ldapsearch()
        wait_for_slapd_to_be_started()

        set_ucr_retry_count(0)
        print_test_header("Case 4: No server restart. "
                          "Perform search. Retry count is 0.")
        perform_univention_ldapsearch()

        print_test_header("Case 5: Stop and start slapd with 5 secs "
                          "delay. Perform search. Retry count is 0.")
        print("Expecting that search case won't work, as retry count is 0 "
              "and start delay is 5.")
        stop_slapd()
        start_with_delay(5)
        perform_univention_ldapsearch(True)  # fail on success
    finally:
        restore_retry_count()
        # try to restore slapd systemd status
        Popen(('systemctl', 'daemon-reload')).wait()
        Popen(('service', 'slapd', 'stop')).wait()
        Popen(('service', 'slapd', 'start')).wait()
        sleep(5)


if __name__ == '__main__':
    """
    Tests that reconnect of univention-ldapsearch works with slapd restart.
    """
    ucr_retry_count = UCR.get('ldap/client/retry/count')
    print(("Saving initial 'ldap/client/retry/count' UCR setting =",
          ucr_retry_count))
    base_dn = UCR.get('ldap/base')

    main()

    # Wait for some seconds otherwise the following test case will fail Bug #45828
    sleep(5)
