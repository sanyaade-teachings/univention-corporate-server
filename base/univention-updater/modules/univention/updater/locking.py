#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2008-2024 Univention GmbH
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
"""Univention Updater locking"""


import os
import sys
from contextlib import contextmanager
from time import sleep


try:
    from time import monotonic  # type: ignore
except ImportError:
    from monotonic import monotonic  # type: ignore

from errno import EEXIST, ENOENT, ESRCH


try:
    from types import TracebackType  # noqa: F401
    from typing import Optional, Type  # noqa: F401
except ImportError:
    pass
from .errors import UpdaterException


FN_LOCK_UP = '/var/lock/univention-updater'
FN_LOCK_APT = "/var/run/apt-get.lock"


class LockingError(UpdaterException):
    """
    Signal other updater process running.

    >>> raise LockingError(1, "Invalid PID")  # doctest: +ELLIPSIS,+IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    univention.updater.locking.LockingError: Another updater process 1 is currently running according to ...: Invalid PID
    """

    def __str__(self):
        # type: () -> str
        return "Another updater process %s is currently running according to %s: %s" % (
            self.args[0],
            FN_LOCK_UP,
            self.args[1],
        )


class UpdaterLock(object):
    """Context wrapper for updater-lock :file:`/var/lock/univention-updater`."""

    def __init__(self, timeout=0):
        # type: (int) -> None
        self.timeout = timeout
        self.lock = 0

    def __enter__(self):
        # type: () -> UpdaterLock
        try:
            self.lock = self.updater_lock_acquire()
            return self
        except LockingError as ex:
            print(ex, file=sys.stderr)
            sys.exit(5)

    def __exit__(self, exc_type, exc_value, traceback):
        # type: (Optional[Type[BaseException]], Optional[BaseException], Optional[TracebackType]) -> None
        if not self.updater_lock_release():
            print('WARNING: updater-lock already released!', file=sys.stderr)

    def updater_lock_acquire(self):
        # type: () -> int
        """
        Acquire the updater-lock.

        :returns: 0 if it could be acquired within <timeout> seconds, >= 1 if locked by parent.
        :rtype: int
        :raises EnvironmentError: on file system access errors.
        :raises LockingError: on invalid PID or timeout.
        """
        deadline = monotonic() + self.timeout
        lock_pid = 0
        while True:
            try:
                lock_fd = os.open(FN_LOCK_UP, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
                my_pid = b"%d\n" % os.getpid()
                bytes_written = os.write(lock_fd, my_pid)
                assert bytes_written == len(my_pid)
                os.close(lock_fd)
                return 0
            except OSError as ex:
                if ex.errno != EEXIST:
                    raise

            try:
                lock_fd = os.open(FN_LOCK_UP, os.O_RDONLY | os.O_EXCL)
                try:
                    lock_pid_b = os.read(lock_fd, 11)  # sizeof(s32) + len('\n')
                finally:
                    os.close(lock_fd)
            except OSError as ex:
                if ex.errno != ENOENT:
                    raise
            else:
                try:
                    lock_pid_s = lock_pid_b.decode('ASCII').strip()
                except UnicodeDecodeError:
                    raise LockingError(lock_pid_b, "Invalid PID")

                if not lock_pid_s:
                    print('Empty lockfile %s, removing.' % (FN_LOCK_UP,), file=sys.stderr)
                    os.remove(FN_LOCK_UP)
                    continue  # redo acquire

                try:
                    lock_pid = int(lock_pid_s)
                except ValueError:
                    raise LockingError(lock_pid_s, "Invalid PID")

                if lock_pid == os.getpid():
                    return 0

                if lock_pid == os.getppid():  # u-repository-* called from u-updater
                    return 1

                try:
                    os.kill(lock_pid, 0)
                except OSError as ex:
                    if ex.errno == ESRCH:
                        print('Stale PID %d in lockfile %s, removing.' % (lock_pid, FN_LOCK_UP), file=sys.stderr)
                        os.remove(FN_LOCK_UP)
                        continue  # redo acquire
                # PID is valid and process is still alive...

            if monotonic() > deadline:
                raise LockingError(lock_pid, "Check lockfile")
            else:
                sleep(1)

    def updater_lock_release(self):
        # type: () -> bool
        """
        Release the updater-lock.

        :returns: True if it has been unlocked (or decremented when nested), False if it was already unlocked.
        :rtype: bool
        """
        if self.lock > 0:
            # parent process still owns the lock, do nothing and just return success
            return True
        try:
            os.remove(FN_LOCK_UP)
            return True
        except OSError as error:
            if error.errno == ENOENT:
                return False
            else:
                raise


@contextmanager
def apt_lock(timeout=300, out=sys.stdout):
    """
    Acquire and release lock for APT.

    :param timeout: Time to wait.
    :param out: Output stream for progress and error messages.
    """
    for count in range(timeout, 0, -1):
        if not os.path.exists(FN_LOCK_APT):
            break
        print("\r%3d Waiting for updater lock %s ..." % (count, FN_LOCK_APT), end="", file=out)
        sleep(1)
    else:
        print("Updater is still locked: %s" % (FN_LOCK_APT,), file=out)
        # FIXME: Abort?

    open(FN_LOCK_APT, "w").close()
    yield None
    if os.path.exists(FN_LOCK_APT):
        os.unlink(FN_LOCK_APT)
