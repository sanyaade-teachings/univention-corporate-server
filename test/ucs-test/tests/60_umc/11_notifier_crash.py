#!/usr/share/ucs-test/runner python3
## desc: Test python-notifer does not crash anymore
## roles:
##  - domaincontroller_master
## packages:
##  - python3-notifier
## bugs: [40510]
## exposure: safe

import subprocess

import notifier

fd = None


def on_read(sock):
	print('on_read')
	return True


def on_timer():
	print('on_timer')
	notifier.socket_remove(fd)
	return True


notifier.init()
p = subprocess.Popen('python3 -c "import sys; sys.stdin.read()"', shell=True, stdin=subprocess.PIPE)
fd = p.stdin.fileno()
notifier.socket_add(fd, on_read)
notifier.timer_add(0, on_timer)
p.communicate(b'A')
notifier.step()  # if bug 40510 is not fixed, the test crashes here with a KeyError exception
notifier.step()
