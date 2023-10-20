#!/usr/share/ucs-test/runner python3
## desc: Tests rate limit of Univention Self Service
## tags: [apptest, SKIP]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-self-service
##   - univention-self-service-passwordreset-umc

import contextlib
from subprocess import call
from time import sleep

from test_self_service import capture_mails, self_service_user

from univention.config_registry import handler_set, handler_unset
from univention.lib.umc import ServiceUnavailable
from univention.testing.ucr import UCSTestConfigRegistry as UCR


LIMIT_TOTAL_MINUTE = 'umc/self-service/passwordreset/limit/total/minute'
LIMIT_TOTAL_HOUR = 'umc/self-service/passwordreset/limit/total/hour'
LIMIT_TOTAL_DAY = 'umc/self-service/passwordreset/limit/total/day'
LIMIT_USER_MINUTE = 'umc/self-service/passwordreset/limit/per_user/minute'
LIMIT_USER_HOUR = 'umc/self-service/passwordreset/limit/per_user/hour'
LIMIT_USER_DAY = 'umc/self-service/passwordreset/limit/per_user/day'


class Main:

    def __init__(self):
        handler_unset([LIMIT_TOTAL_MINUTE, LIMIT_TOTAL_HOUR, LIMIT_TOTAL_DAY, LIMIT_USER_MINUTE, LIMIT_USER_HOUR, LIMIT_USER_DAY])
        with capture_mails():
            self.test_total_limits()
            self.test_user_limits()

    def test_total_limits(self):
        print('########################### test_total_limits ##############################')
        cuser = self_service_user(email='user@localhost')
        with cuser as user, set_limits(total_minute=1):
            assert fail_after(user, 1, 'one minute'), LIMIT_TOTAL_MINUTE
            wait(minutes=1)
            dont_fail(user)

    def test_user_limits(self):
        print('########################### test_user_limits ##############################')
        cuser1 = self_service_user(email='user1@localhost')
        cuser2 = self_service_user(email='user2@localhost')
        limits = set_limits(total_minute=7, user_minute=3)
        with cuser1 as user1, cuser2 as user2, limits:
            assert fail_after(user1, 3, 'one minute')
            assert fail_after(user2, 2, 'one minute')
            wait(minutes=1)
            dont_fail(user2)


@contextlib.contextmanager
def set_limits(total_minute=None, total_hour=None, total_day=None, user_minute=None, user_hour=None, user_day=None):
    print('setting limit to %s' % locals())
    with UCR(), resetting_limits():
        total_minute = (LIMIT_TOTAL_MINUTE, total_minute)
        total_hour = (LIMIT_TOTAL_HOUR, total_hour)
        total_day = (LIMIT_USER_DAY, total_day)
        user_minute = (LIMIT_USER_MINUTE, user_minute)
        user_hour = (LIMIT_USER_HOUR, user_hour)
        user_day = (LIMIT_USER_DAY, user_day)
        args = [total_minute, total_hour, total_day, user_minute, user_hour, user_day]
        handler_set([f'{key}={val}' for key, val in args if val is not None])
        handler_unset([key for key, val in args if val is None])
        yield


def fail_after(user, x, retry_after):
    print('We should fail after', x)
    for i in range(x):
        print('Attempt (we shall not fail)', i + 1)
        user.send_token('email')

    try:
        print('We should fail now...')
        user.send_token('email')
    except ServiceUnavailable as exc:
        retry_after = f'Please retry in {retry_after}.'
        assert str(exc)
        print('Yippie, failed!')
        return True
    raise AssertionError('limit not evaluated')


def dont_fail(user):
    print('Now we should not fail anymore')
    user.send_token('email')
    print('Did not fail ;)')


@contextlib.contextmanager
def resetting_limits():
    reset_server_limits()
    try:
        yield
    finally:
        reset_server_limits()


def reset_server_limits():
    assert call(['deb-systemd-invoke', 'restart', 'memcached'], close_fds=True) == 0
    assert call(['deb-systemd-invoke', 'restart', 'univention-management-console-server'], close_fds=True) == 0
    print('Waiting for umc restart')
    sleep(3)


def wait(minutes):
    # TODO: set the server time otherwise this test blocks that long
    print('Waiting %d minutes' % (minutes,))
    sleep((minutes * 60) + 1)


if __name__ == '__main__':
    Main()
