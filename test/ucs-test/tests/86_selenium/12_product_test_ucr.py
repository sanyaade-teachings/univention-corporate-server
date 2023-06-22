#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
## desc: check setting UCR variables
## packages:
##  - univention-management-console-module-ucr
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import subprocess
import tempfile
import time

from selenium.webdriver.common.by import By

from univention.lib.i18n import Translation
from univention.testing import selenium


_ = Translation('ucs-test-selenium').translate


SEARCHES = [
    {
        'pattern': '*tmpKey',
        'expected_results': 2,
    },
    {
        'pattern': 'tmpKey',
        'expected_results': 4,
    },
    {
        'pattern': '*tmpDesc',
        'expected_results': 2,
    },
    {
        'pattern': '*tmpDesc*',
        'expected_results': 4,
    },
    {
        'pattern': '*tmpVal',
        'expected_results': 2,
    },
    {
        'pattern': 'tmpVal*',
        'expected_results': 2,
    },
    {
        'pattern': '*tmpVal*',
        'expected_results': 4,
    },
    {
        'pattern': 'tmpVal',
        'expected_results': 4,
    },
]


def create_testing_ucr_variables(ucr_variable_file):
    ucr_variable_file.write(
        b"[umc_test/foo_tmpKey]\n"
        b"Description[de]=This is a test-description. foo_tmpDesc\n"
        b"Description[en]=This is a test-description. foo_tmpDesc\n"
        b"Type=str\n"
        b"Categories=system-base\n"
        b"\n"
        b"[umc_test/tmpKey_foo]\n"
        b"Description[de]=This is a test-description. tmpDesc_foo\n"
        b"Description[en]=This is a test-description. tmpDesc_foo\n"
        b"Type=str\n"
        b"Categories=system-base\n"
        b"\n"
        b"[umc_test/foo_tmpKey_bar]\n"
        b"Description[de]=This is a test-description. foo_tmpDesc_bar\n"
        b"Description[en]=This is a test-description. foo_tmpDesc_bar\n"
        b"Type=string\n"
        b"Categories=service-software-management\n"
        b"\n"
        b"[umc_test/tmpKey]\n"
        b"Description[de]=This is a test-description. tmpDesc\n"
        b"Description[en]=This is a test-description. tmpDesc\n"
        b"Type=str\n"
        b"Categories=management-umc\n",
    )
    ucr_variable_file.flush()

    subprocess.call(['ucr', 'set', 'umc_test/foo_tmpKey=foo_tmpVal'])
    subprocess.call(['ucr', 'set', 'umc_test/tmpKey_foo=tmpVal_foo'])
    subprocess.call(['ucr', 'set', 'umc_test/foo_tmpKey_bar=foo_tmpVal_bar'])
    subprocess.call(['ucr', 'set', 'umc_test/tmpKey=tmpVal'])


class UcrSearchError(Exception):
    pass


class UMCTester(object):

    def test_umc(self):
        self.selenium.do_login()
        self.selenium.open_module(_('Univention Configuration Registry'))
        self.selenium.wait_for_text(_('apache'))
        self.selenium.wait_until_all_standby_animations_disappeared()

        self.test_ucr_search(SEARCHES)
        self.test_setting_a_variable('umc_test/foo_tmpKey_bar', 'testValue')
        self.test_category_filter()

    def test_ucr_search(self, searches):
        for search in searches:
            search_results = self.get_umc_search_results(search['pattern'])
            if len(search_results) != search['expected_results']:
                raise UcrSearchError(
                    'The UMC-UCR search %r found %d entries instead of the '
                    'expected %d.'
                    % (
                        search['pattern'],
                        len(search_results),
                        search['expected_results'],
                    ),
                )

    def test_setting_a_variable(self, ucr_key, value):
        self.selenium.enter_input('pattern', ucr_key)
        self.selenium.submit_input('pattern')
        self.selenium.wait_until_all_standby_animations_disappeared()

        self.selenium.click_grid_entry(ucr_key)
        self.selenium.wait_for_text(_("Edit UCR variable"))
        self.selenium.wait_until_all_standby_animations_disappeared()
        self.selenium.enter_input(_('value'), value)
        self.selenium.click_button(_('Save'))
        # This is needed, because the grid needs time for the automatic refresh.
        time.sleep(5)
        self.selenium.wait_until_all_standby_animations_disappeared()
        if value == "":
            self.selenium.click_button(_('Store empty string'))
        time.sleep(5)
        self.selenium.wait_until_all_standby_animations_disappeared()

        ucr_result = self.get_ucr_cli_search_results(ucr_key)
        if ucr_result[ucr_key] != value:
            raise UcrSearchError(
                "Setting a variable's value via the UMC-UCR did not work.",
            )

    def test_category_filter(self):
        self.selenium.enter_input_combobox('category', _('Base Settings'))
        result_count = len(self.get_umc_search_results('tmpKey'))
        expected_result_count = 2
        if result_count != expected_result_count:
            raise UcrSearchError(
                "Filtering the results of an UMC-UCR search by category did not"
                " work. Got %d instead of the expected %d results."
                % (result_count, expected_result_count),
            )

    def get_ucr_cli_search_results(self, pattern):
        search_result_string = subprocess.check_output(
            ['ucr', 'search', '--brief', '--all', pattern],
        ).decode()
        result_strings = search_result_string.split('\n')[:-1]
        search_results = {}
        for result in result_strings:
            # Such 'template' variables are not shown in the UMC, so they'll be
            # filtered out here, too.
            if '.*' in result:
                continue
            key, value = result.split(':', 1)
            key, value = key.strip(), value.strip()
            if value == '<empty>':
                value = u''
            search_results[key] = value
        return search_results

    def get_umc_search_results(self, pattern):
        self.selenium.enter_input('pattern', pattern)
        self.selenium.submit_input('pattern')
        self.selenium.wait_until_standby_animation_appears_and_disappears()
        grid_rows = self.selenium.driver.find_elements(
            By.XPATH,
            '//*[contains(concat(" ", normalize-space(@class), " "), '
            '" dgrid-row ")][@role="row"]',
        )
        search_results = {}
        for row in grid_rows:
            search_results[self.get_key(row)] = self.get_value(row)
        return search_results

    def get_key(self, grid_row):
        elem = grid_row.find_element(
            By.XPATH,
            './/*[contains(concat(" ", normalize-space(@class), " "), '
            '" field-key ")]',
        )
        return elem.text

    def get_value(self, grid_row):
        elem = grid_row.find_element(
            By.XPATH,
            './/*[contains(concat(" ", normalize-space(@class), " "), '
            '" field-value ")]',
        )
        return elem.text


if __name__ == '__main__':
    f = tempfile.NamedTemporaryFile(
        suffix=".cfg",
        dir="/etc/univention/registry.info/variables/",
    )
    with f as ucr_variable_file, selenium.UMCSeleniumTest() as s:
        umc_tester = UMCTester()
        umc_tester.selenium = s

        create_testing_ucr_variables(ucr_variable_file)
        umc_tester.test_umc()
