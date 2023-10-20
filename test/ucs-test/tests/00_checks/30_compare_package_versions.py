#!/usr/share/ucs-test/runner python3
## desc: Check that package versions of the current release are higher than for the previous.
## bugs: [36369]
## roles: [domaincontroller_master]
## tags: [producttest]
## exposure: safe

from gzip import open as gzip_open
from optparse import OptionParser
from os import makedirs, path
from re import IGNORECASE, compile as re_compile
from shutil import Error as shutil_Error, rmtree
from tempfile import mkdtemp
from time import sleep
from urllib import urlopen, urlretrieve
from urllib.error import ContentTooShortError

from apt_pkg import init as apt_init, version_compare
from lxml.html import fromstring
from packaging.version import Version

from univention.testing import utils


cleanup_folders = []  # list of the folders to be removed after the test
total_errors = 0

MAJOR_VERSION_RE = re_compile(r'(\d+\.{0,1})+$')  # to match 3.2
MINOR_VERSION_RE = re_compile(r'(\d+\.{0,1}-{0,1})+$')  # to match 3.2-4
ERRATA_VERSION_RE = re_compile(r'(.*-errata)+$', IGNORECASE)  # to match 3.2-4-errata


class PackageEntry:

    def __init__(self, package=None, version=None, filename=None, sourcepkg=None, ucs_version=None):
        self.package = package
        self.version = version
        self.filename = filename
        self.sourcepkg = sourcepkg
        self.ucs_version = ucs_version

    def _get_value(self, line):
        return line.split(': ', 1)[1]

    def scan(self, entry, ucs_version):
        if ucs_version:
            self.ucs_version = ucs_version

        for line in entry.splitlines():
            if line.startswith('Package: '):
                self.package = self._get_value(line)
            elif line.startswith('Version: '):
                self.version = self._get_value(line)
            elif line.startswith('Filename: '):
                self.filename = self._get_value(line)
            elif line.startswith('Source: '):
                self.sourcepkg = self._get_value(line)

    def is_ok(self):
        return bool(self.package) and bool(self.version)


def perform_cleanup():
    """Removes all the folders/files located in the 'cleanup_folders' list."""
    print("\nPerforming cleanup after the test:")

    for folder in cleanup_folders:
        print("Removing folder:", folder)
        try:
            rmtree(folder, False)

        except (shutil_Error, OSError) as exc:
            print("\nAn %r Error occurred while trying to remove a '%s'. "
                  "Probably folder/files were not removed."
                  % (exc, folder))


def download_packages_file(url, version, arch, temp_directory):
    """
    Downloads a 'Packages.gz' as the given url into the
    'temp_directory/version/arch/' folder.
    """
    file_name = temp_directory + '/' + version + '/'  # only part of the path that has version
    file_path = file_name + arch + '/Packages.gz'  # a complete path to the 'Packages.gz' file

    url += version + '/' + arch + '/Packages.gz'
    print("\nDownloading:", url)

    try:
        makedirs(file_name + arch)
    except OSError as exc:
        utils.fail("An Error occurred while creating the directory structure "
                   "at '%s' for the Packages.gz file: %r" % (file_path, exc))

    try:
        urlretrieve(url, file_path)  # noqa: S310
    except ContentTooShortError as exc:
        print("An %r Error occurred, probably the connection was lost. "
              "Performing a new attempt in 10 seconds." % exc)
        sleep(10)
        urlretrieve(url, file_path)  # noqa: S310
    except OSError as exc:
        print("An %r Error occurred, probably the connection cannot be "
              "established or the url is incorrect. "
              "Skipping the url '%s'." % (exc, url))
        return

    if path.exists(file_path):
        return file_name


def load_packages_file(filename, target_dict, ucs_version):
    """
    Reads the given 'filename' Packages.gz file.
    Creates a entry object for each found package and fills the target_dict.
    """
    if not path.exists(filename):
        print("Error: file %s does not exist" % filename)
        return

    try:
        # first try to open it as a .gzip
        packages_file = gzip_open(filename, 'r')
    except OSError:
        # otherwise open it as a usual file
        packages_file = open(filename)

    try:
        content = packages_file.read()
        if not content:
            utils.fail("The '%s' file is either empty or cannot be read."
                       % filename)

        packages_file.close()
    except (ValueError, OSError) as exc:
        utils.fail("An %r Error occurred while trying to read and close the "
                   "file '%s'" % (exc, filename))

    for entry in content.split('\n\n'):
        # scan each entry in the 'filename'
        item = PackageEntry()
        item.scan(entry, ucs_version)

        if item.is_ok():
            if item.package in target_dict:
                if version_compare(target_dict[item.package].version, item.version) < 0:
                    target_dict[item.package] = item
            else:
                target_dict[item.package] = item


def load_version(url):
    """
    Selects all minor and errata versions for the given 'url'.
    Downloads respective 'Packages.gz' for each version and
    returns a dict filled with PackageEntries.
    """
    target = {}

    temp = mkdtemp()  # a temp folder to store 'Packages.gz' for each version
    cleanup_folders.append(temp)  # to remove a folder after

    for version in select_minor_levels(url):
        for arch in ('all', 'i386', 'amd64'):
            file_name = download_packages_file(url, version, arch, temp)

            if file_name:
                # only load the packages file when it was downloaded
                print("Loading packages file:", file_name + arch + '/Packages.gz')
                load_packages_file(path.join(file_name, arch, 'Packages.gz'),
                                   target,
                                   'ucs_' + version)
    return target


def compare(old, new):
    """
    Compares 'old' and 'new' versions via apt.
    Prints all the errors detected.
    """
    errors = 0
    package_list = sorted(new.keys())
    src_package_list = set()

    for package in package_list:
        if package in old and version_compare(old[package].version, new[package].version) > 0:
            if errors == 0:
                print('\n---------------------------------------------------------')
                print('  The following packages use a smaller package version:')
                print('---------------------------------------------------------\n')

            print(" Package: %s" % package)
            print(f"   {old[package].ucs_version}: {old[package].version}")
            print(f"   {new[package].ucs_version}: {new[package].version}")

            src_package = new[package].sourcepkg
            if not src_package:
                src_package = package

            src_package_list.add(src_package)

            print("  Source package: %s" % src_package)
            errors += 1

    if errors:
        print("\nAffected source packages:")
        for package in sorted(src_package_list):
            print("  %s" % package)

        print("\nNumber of affected binary packages: %d" % errors)
        print("Number of affected source packages: %d" % len(src_package_list))

        global total_errors
        total_errors += errors


def read_url(url):
    """Returns the 'url' in an easy to parse format for finding links."""
    try:
        connection = urlopen(url)  # noqa: S310
        result = fromstring(connection.read())
    except OSError as exc:
        utils.fail("An %r Error occurred while trying to retrieve '%s' url"
                   % (exc, url))
    connection.close()
    return result


def select_errata_levels(repo_component_url):
    """Returns list of .*-errata levels found in the given 'repo_component_url'."""
    check_erratalevels = []

    for link in read_url(repo_component_url).xpath('//a/@href'):
        if link.endswith('/'):
            link = link[:-1]  # remove the '/' from a link
        if ERRATA_VERSION_RE.match(link):
            check_erratalevels.append('component/' + link)

    return check_erratalevels


def select_minor_levels(repo_major_url):
    """
    Returns the list of minor versions with patch and errata levels as found
    for the given 'repo_major_url'.
    """
    check_patchlevels = []

    for link in read_url(repo_major_url).xpath('//a/@href'):
        if link.endswith('/'):
            link = link[:-1]  # remove the '/' from a link
        if MINOR_VERSION_RE.match(link):
            check_patchlevels.append(link)
        if 'component' in link:
            # add component/errata levels:
            component_link = repo_major_url + link + '/'
            check_patchlevels += select_errata_levels(component_link)

    if len(check_patchlevels) < 1:
        utils.fail("Could not find at least one patch level number in "
                   "the given repository at '%s'" % repo_major_url)

    print("\nThe following patch levels will be checked:", check_patchlevels)
    return check_patchlevels


def select_major_versions_for_test(repo_url):
    """
    Looks into specified 'repo_url' and picks up the two most recent
    major versions (for example 3.2 and 4.0).
    """
    check_versions = []

    for link in read_url(repo_url).xpath('//a/@href'):
        if link.endswith('/'):
            link = link[:-1]  # remove the '/' from a link
        if MAJOR_VERSION_RE.match(link):
            check_versions.append(link)

    if len(check_versions) < 2:
        utils.fail("Could not find at least two version numbers in "
                   "the given repository at '%s'" % repo_url)

    check_versions.sort()  # a list with increasing version numbers

    # return list with only two last versions (i.e. two highest numbers)
    return check_versions[-2:]


def parse_arguments():
    """
    Returns the parsed arguments when test is run interactively via
    'python3 testname ...'
    First an older version should be specified.
    """
    usage = """%progname <old UCS version> <new UCS version>

    Loads all Packages files up to last major version for both given
    (major) versions and compares the available package versions."""

    parser = OptionParser(usage=usage)
    options, args = parser.parse_args()

    if len(args) == 2:
        try:
            old_version = Version(args[0])
            new_version = Version(args[1])
            if new_version < old_version:
                utils.fail("The given new '%s' version cannot be smaller "
                           "than the older '%s' version"
                           % (new_version, old_version))
        except ValueError as exc:
            utils.fail("An %r Error occurred when trying to process parsed "
                       "version numbers" % exc)
        return args

    print("\nThe UCS versions for the test will be determined automatically:")


if __name__ == '__main__':
    """
    Checks that all the packages in the specified remote repositiories for an
    older UCS release have lower version number than for the current UCS ver.
    UCS versions are either picked automatically (two most recent, by default)
    or can be specified as a command-line arguments.
    """
    check_versions = parse_arguments()
    apt_init()  # init the apt

    repositories_to_check = (
        'https://updates-test.software-univention.de/',
        'https://updates.software-univention.de/',
    )

    try:
        for repo_url in repositories_to_check:
            if not check_versions:
                # if no version arguments were given, determine most recent:
                check_versions = select_major_versions_for_test(repo_url)

            print("\nComparing packages for UCS versions %s and %s "
                  "in repository at '%s':"
                  % (check_versions[0], check_versions[1], repo_url))

            # comparing first maintained and than unmaintained sections:
            for repo_type in ('maintained/', 'unmaintained/'):
                print("\nChecking %s packages:" % repo_type[:-1])
                previous_version = repo_url + check_versions[0] + '/' + repo_type
                current_version = repo_url + check_versions[1] + '/' + repo_type

                # comparing determined versions:
                compare(load_version(previous_version),
                        load_version(current_version))
    finally:
        perform_cleanup()
        if total_errors:  # an overall statistics
            utils.fail("There were %d errors detected in total. Please check"
                       " the complete test output." % total_errors)

        print("\nNo errors were detected.\n")
