#
# UCS test
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2013-2024 Univention GmbH
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

from __future__ import annotations

import os
import pwd
import subprocess
import time
from types import TracebackType
from typing import Set, Type


class MailSinkGuard:
    """
    This class is a simple context manager that stops all attached mail sinks
    if the context is left.

    >>> with MailSinkGuard() as msg:
    ...     sink = MailSink('127.0.0.1', 12345, target_dir='/tmp/')
    ...     msg.add(sink)
    """

    def __init__(self) -> None:
        self.mail_sinks: Set[MailSink] = set()

    def add(self, sink: MailSink) -> None:
        self.mail_sinks.add(sink)

    def __enter__(self) -> MailSinkGuard:  # FIXME Py3.9: Self
        return self

    def __exit__(self, exc_type: Type[BaseException] | None, exc_value: BaseException | None, etraceback: TracebackType | None) -> None:
        for mail_sink in self.mail_sinks:
            mail_sink.stop()


class MailSink:
    """
    This class starts an SMTP sink on the specified address/port.
    Each incoming mail will be written to a single file if target_dir is used.
    To write all incoming mails into one file, use filename.

    >>> MailSink.CMD = '/bin/true'  # monkey-patch for unit-testing only
    >>> ms = MailSink('127.0.0.1', 12345, target_dir='/tmp/')
    >>> ms.start()
    *** Starting SMTPSink at 127.0.0.1:12345
    *** ['/bin/true', '-d', '/tmp/%Y%m%d-%H%M%S.', '-u', 'root', '127.0.0.1:12345', '10']
    >>> ms.stop()
    *** SMTPSink at 127.0.0.1:12345 stopped

    >>> ms = MailSink('127.0.0.1', 12345, filename='/tmp/sinkfile.eml')
    >>> ms.start()
    *** Starting SMTPSink at 127.0.0.1:12345
    *** ['/bin/true', '-D', '/tmp/sinkfile.eml', '-u', 'root', '127.0.0.1:12345', '10']
    >>> ms.stop()
    *** SMTPSink at 127.0.0.1:12345 stopped

    >>> with MailSink('127.0.0.1', 12345, filename='/tmp/sinkfile.eml') as ms:
    ...     pass
    *** Starting SMTPSink at 127.0.0.1:12345
    *** ['/bin/true', '-D', '/tmp/sinkfile.eml', '-u', 'root', '127.0.0.1:12345', '10']
    *** SMTPSink at 127.0.0.1:12345 stopped
    """

    CMD = '/usr/sbin/smtp-sink'  # use postfix' smtp-sink tool

    def __init__(self, address: str, port: int, filename: str | None = None, target_dir: str | None = None, fqdn: str | None = None) -> None:
        self.address = address
        self.port = port
        self.filename = filename
        self.target_dir = target_dir
        self.process: subprocess.Popen | None = None
        self.fqdn = fqdn

    def __enter__(self) -> MailSink:  # FIXME Py3.9: Self
        self.start()
        return self

    def __exit__(self, exc_type: Type[BaseException] | None, exc_value: BaseException | None, etraceback: TracebackType | None) -> None:
        self.stop()

    def start(self) -> None:
        print(f'*** Starting SMTPSink at {self.address}:{self.port}')
        cmd = [self.CMD]
        if self.filename is not None:
            cmd.extend(['-D', self.filename])
        elif self.target_dir is not None:
            cmd.extend(['-d', os.path.join(self.target_dir, '%Y%m%d-%H%M%S.')])
        else:
            cmd.extend(['-d', os.path.join('./%Y%m%d-%H%M%S.')])
        if self.fqdn:
            cmd.extend(['-h', self.fqdn])
        if os.geteuid() == 0:
            cmd.extend(['-u', pwd.getpwuid(os.getuid()).pw_name])
        cmd.append(f'{self.address}:{self.port}')
        cmd.append('10')
        print(f'*** {cmd!r}')
        self.process = subprocess.Popen(cmd, stderr=subprocess.STDOUT)

    def stop(self) -> None:
        if self.process is not None:
            self.process.terminate()
            time.sleep(1)
            self.process.kill()
            print(f'*** SMTPSink at {self.address}:{self.port} stopped')
            self.process = None


if __name__ == '__main__':
    # ms = MailSink('127.0.0.1', 12345, target_dir='/tmp/')
    ms = MailSink('127.0.0.1', 12345, filename='/tmp/sink.eml')
    print('Starting sink')
    ms.start()
    print('Waiting')
    time.sleep(25)
    print('Stopping sink')
    ms.stop()
    print('Waiting')
    time.sleep(5)
