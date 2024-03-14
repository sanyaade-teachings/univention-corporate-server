#!/usr/share/ucs-test/runner /usr/share/ucs-test/locust-docker ScenarioLogin
# /usr/share/ucs-test/runner /usr/share/ucs-test/locust --spawn-rate 0.5 -u 100 -t 20m --csv ScenarioLogin --html ScenarioLogin.html ScenarioLogin
## desc: "Replay a captured HAR of the login flow"
## exposure: safe
## tags: [producttest, SKIP]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## env:
##   LOCUST_SPAWN_RATE: "0.5"
##   LOCUST_RUN_TIME: "20m"
##   LOCUST_USERS: "100"
##   LOCUST_USER_CLASSES: ScenarioLogin
##   WAIT_MIN: "10"
##   WAIT_MAX: "20"

import logging
import os
from urllib.parse import urlparse

from locust import HttpUser, between, task
from utils import login_via_saml, replay_har


USE_TASK = os.environ.get('USE_TASK', '0') == '1'
WAIT_MIN = int(os.environ.get('WAIT_MIN', '10'))
WAIT_MAX = int(os.environ.get('WAIT_MAX', '20'))


# TODO: use FastHttpUser instead of HttpUser
# https://docs.locust.io/en/stable/increase-performance.html
class ScenarioLogin(HttpUser):
    wait_time = between(WAIT_MIN, WAIT_MAX)

    def on_start(self):
        if USE_TASK:
            return
        try:
            self.do_umc_login()
        finally:
            self.client.close()

    @task
    def login(self):
        if not USE_TASK:
            return
        try:
            self.do_umc_login()
        finally:
            self.client.cookies.clear()

    def do_umc_login(self):
        host = urlparse(self.client.base_url).netloc
        logging.info('First page...')
        replay_har('hars/univention_portal.har', self.client, host=host)
        replay_har('hars/ucs-sso_login.har', self.client, host=host)
        umc_session_id = login_via_saml(self.client)
        if umc_session_id is None:
            return

        logging.info(f'Created new session with Session: {umc_session_id}')
        replay_har('hars/login_done.har', self.client, host=host, session_id=umc_session_id)
        logging.info('Done...')