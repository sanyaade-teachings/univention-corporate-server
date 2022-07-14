#!/usr/share/ucs-test/runner python3
## desc: Logrotation should trigger UMC components to reopen their logfiles
## packages:
##  - univention-management-console
##  - univention-management-console-frontend
## exposure: dangerous
## bugs: [38143, 37317]

import os
import os.path
from subprocess import PIPE, Popen, call
from time import sleep

from univention.testing.utils import fail


class LogrotateError(Exception):
	pass


class LogrotateService(object):

	def __init__(self, service, logfile_pattern):
		self.service = service
		self.logfile_pattern = logfile_pattern
		self.old_stat = None

	@property
	def pgrep_pattern(self):
		return r'^/usr/bin/python.*%s.*' % (self.service,)

	def pid(self):
		process = Popen(['pgrep', '-x', '-f', self.pgrep_pattern], stdout=PIPE)
		stdout, _stderr = process.communicate()
		if process.returncode:
			raise LogrotateError('pgrep %s failed with returncode %s' % (self.service, process.returncode))
		pids = [int(pid) for pid in stdout.splitlines() if pid.strip()]
		if not pids:
			raise LogrotateError('service %s is not started.' % (self.service,))
		if len(pids) != 1:
			raise LogrotateError('multiple services of %s are started: pids=%s' % (self.service, pids))
		return pids[0]

	def logfile(self):
		pid = self.pid()
		for file_ in os.listdir('/proc/%d/fd/' % (pid,)):
			file_ = os.path.join('/proc/%d/fd/' % (pid,), file_)
			if os.path.islink(file_) and os.readlink(file_).startswith(self.logfile_pattern):
				return file_
		print('No logfile for service %s found.' % (self.service,))

	def stat(self, logfile):
		try:
			stat = os.stat(logfile)
			print(logfile, stat)
		except OSError:
			raise LogrotateError('%s does not exists (service=%s)' % (logfile, self.service))
		return stat

	def service_restart(self):
		call(['invoke-rc.d', os.path.basename(self.service), 'restart'])
		sleep(1)  # give time to restart

	def pre(self):
		self.service_restart()
		self.old_stat = self.stat(self.logfile())

	def post(self):
		for i in range(10):
			if i:
				sleep(1)
			logfile = self.logfile()
			if not logfile:
				continue
			new_stat = self.stat(logfile)
			if not os.path.samestat(self.old_stat, new_stat):
				return
		raise LogrotateError('Logrotate was executed, the service %s did not reopen the logfile %s.' % (
			self.service, logfile))


def logrotate():
	cmd = ('logrotate', '-v', '-f', '/etc/logrotate.d/univention-management-console')
	if call(cmd):
		raise LogrotateError('logrotate failed: %r' % (cmd,))


def main():
	services = [
		LogrotateService('/usr/sbin/univention-management-console-server', '/var/log/univention/management-console-server.log'),
		LogrotateService('/usr/sbin/univention-management-console-web-server', '/var/log/univention/management-console-web-server.log'),
	]
	try:
		for service in services:
			service.pre()
		logrotate()
		for service in services:
			service.post()
	except LogrotateError as exc:
		fail('ERROR: %s' % (exc,))


if __name__ == '__main__':
	main()
