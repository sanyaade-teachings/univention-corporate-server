#!/usr/share/ucs-test/runner python3
## desc: Check if requests are answered with an error code after killing ucstest module
## roles:
##  - domaincontroller_master
## packages:
##  - univention-management-console
##  - univention-management-console-frontend
##  - ucs-test-umc-module
## exposure: dangerous

import http.client as httplib
import socket
import ssl
import subprocess
import time

import psutil

import univention.testing.utils as utils
from univention.management.console.modules.ucstest import joinscript, unjoinscript
from univention.testing.umc import Client

NUMBER_OF_CONNECTIONS = 8
RESPONSE_STATUS_CODES = (510, 511)


def kill_ucstest():
	search_mask = set(['/usr/sbin/univention-management-console-module', '-m', 'ucstest'])
	for process in psutil.process_iter():
		if not (search_mask - set(process.cmdline())):
			print('Found module process %s %r and killing it ...' % (process.pid, process.cmdline(),))
			process.kill()
			try:  # if kill did not succeed, terminate
				process.terminate()
			except psutil.NoSuchProcess:
				pass
	time.sleep(0.5)
	for process in psutil.process_iter():
		if not (search_mask - set(process.cmdline())):
			assert False, 'ERROR: ... module process %s %r is still there, this should not happen!' % (process.pid, process.cmdline(),)


def restart_web_server():
	subprocess.call(['systemctl', 'restart', 'univention-management-console-web-server', 'univention-management-console-server', 'apache2'])


class AsyncClient(Client):

	def async_request(self, path):
		cookie = '; '.join(['='.join(x) for x in self.cookies.items()])
		headers = dict(self._headers, **{'Cookie': cookie, 'Content-Type': 'application/json'})
		headers['X-XSRF-Protection'] = self.cookies.get('UMCSessionId', '')
		connection = httplib.HTTPSConnection(self.hostname, timeout=10)
		print('*** POST to /univention/command/%s with headers=%r' % (path, headers))
		connection.request('POST', '/univention/command/%s' % path, '{}', headers=headers)
		return connection


def main():
	print('Setting up the connections and sending requests...')
	connections = [
		AsyncClient.get_test_connection(timeout=10).async_request('ucstest/norespond')
		for i in range(NUMBER_OF_CONNECTIONS)
	]
	time.sleep(2)

	print('Killing module process...')
	kill_ucstest()
	time.sleep(2)

	print('Verfying that requests are answered with an error code...')
	success = True
	for i_connection in connections:
		try:
			response = i_connection.getresponse()
			print('*** RESPONSE Status=%s; body=\n%r\n***' % (response.status, response.read()))
			if response.status not in RESPONSE_STATUS_CODES:
				print('ERROR: Unexpected status of response %s (expected was one of %s)' % (response.status, RESPONSE_STATUS_CODES))
				success = False
		except (socket.timeout, ssl.SSLError):
			print('ERROR: request timed out')

	if not success:
		utils.fail('ERROR: Requests are not answered with an error code')


if __name__ == '__main__':
	joinscript()
	try:
		main()
	finally:
		restart_web_server()
		unjoinscript()
