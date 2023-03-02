#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright (C) 2008-2023 Univention GmbH
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

import argparse
import os
import re
import sys
from errno import ENOENT
from fnmatch import fnmatch
from os.path import normpath, relpath
from typing import (  # noqa: F401
    Any, Callable, Dict, Iterable, Iterator, List, Mapping, Match, Optional, Pattern, Set, Tuple,
)


try:
    from junit_xml import TestCase  # type: ignore

    TestCase('test', file=__file__, line=1)
    JUNIT = True
except (ImportError, TypeError):
    JUNIT = False

    class TestCase:  # type: ignore
        def __init__(self, name: str, stdout: str | None = None, file: str | None = None, line: int | None = None) -> None:
            pass

        def add_error_info(self, message: str | None = None, output: str | None = None, error_type: str | None = None) -> None:
            pass

        def add_skipped_info(self, message: str | None = None, output: str | None = None) -> None:
            pass


RE_OVERRIDE = re.compile(
    r'''^
    (?P<module> \d+-[BEFNW]?\d+)
    (?: [:]
        (?: \s* (?P<pattern> .+?) \s*
            (?: [:] \s* (?P<linenumber> \d+)
            )?
        )?
    )?
    $''', re.VERBOSE)


RESULT_UNKNOWN = -1
RESULT_OK = 0
RESULT_WARN = 1
RESULT_ERROR = 2
RESULT_INFO = 3
RESULT_STYLE = 4

RESULT_INT2STR: Dict[int, str] = {
    RESULT_UNKNOWN: 'U',
    RESULT_OK: 'OK',
    RESULT_WARN: 'W',
    RESULT_ERROR: 'E',
    RESULT_INFO: 'I',
    RESULT_STYLE: 'S',
}

MsgIds = Dict[str, Tuple[int, str]]

RE_MSGID = re.compile(r'\d{4}-[BEFNW]?\d+')
RE_IGNORE = re.compile(r'\s+ ucslint :? \s* (?: ({msgid} (?: [, ]+ {msgid})*) \s* )? $'.format(msgid=RE_MSGID.pattern), re.VERBOSE)


def clean_id(idstr: str) -> str:
    """
    Format message ID string.

    :param idstr: message identifier.
    :returns: formatted message identifier.

    >>> clean_id('1-2')
    '0001-2'
    """
    if '-' not in idstr:
        raise ValueError('no valid id (%s) - missing dash' % idstr)
    modid, msgid = idstr.strip().split('-', 1)
    return '%s-%s' % (clean_modid(modid), clean_msgid(msgid))


def clean_modid(modid: str) -> str:
    """
    Format module ID string.

    :param modid: module number.
    :returns: formatted module number.

    >>> clean_modid('1')
    '0001'
    """
    if not modid.isdigit():
        raise ValueError('modid contains invalid characters: %s' % modid)
    return '%04d' % (int(modid))


def clean_msgid(msgid: str) -> str:
    """
    Format message ID string.

    :param msgid: message number.
    :returns: formatted message number.

    >>> clean_msgid('01')
    '1'
    """
    if not msgid.isdigit():
        raise ValueError('msgid contains invalid characters: %s' % msgid)
    return '%d' % int(msgid)


def noqa(line: str) -> Callable[[str], bool]:
    """
    Check for lines to be ignored by ` ucslint: 0000-0`.

    >>> noqa('')('0000-0')
    False
    >>> noqa('# ucslint')('0000-0')
    True
    >>> noqa('# ucslint: 0000-0')('0000-0')
    True
    >>> noqa('# ucslint: 0000-1')('0000-0')
    False
    >>> noqa('# ucslint: 0000-0, 0000-1')('0000-0')
    True
    """
    match = RE_IGNORE.search(line)
    if not match:
        return lambda issue: False

    ignore = match.group(1)
    if not ignore:
        return lambda issue: True

    issues = set(RE_MSGID.findall(ignore))
    return lambda issue: issue in issues


def line_regexp(text: str, regexp: Pattern[str]) -> Iterator[Tuple[int, int, Match[str]]]:
    """
    Find all matches and return row and colum number.

    :param text: The text to seach in.
    :param regexp: Compiled regular excpression.
    :returns: Iterator returning 3-tuples (row, col, match)
    """
    row = 1
    col = 1
    pos = 0
    for match in regexp.finditer(text):
        start, end = match.span()
        while pos < start:
            if text[pos] == "\n":
                col = 1
                row += 1
            else:
                col += 1
            pos += 1

        yield (row, col, match)


class UPCMessage:
    """
    Univention Policy Check message.

    :param id: Message identifier.
    :param msg: Message test.
    :param filename: Associated file name.
    :param row: Associated line number.
    :param col: Associated column number.
    """

    def __init__(self, id_: str, msg: str, filename: str | None = None, row: int | None = None, col: int | None = None) -> None:
        self.id = id_
        self.msg = msg
        self.filename = filename
        self.row = row
        self.col = col

        if self.filename is not None and self.filename.startswith('./'):
            self.filename = self.filename[2:]

    def __str__(self) -> str:
        if self.filename:
            s = '%s' % self.filename
            if self.row is not None:
                s += ':%s' % self.row
                if self.col is not None:
                    s += ':%s' % self.col
            return f'{self.id}: {s}: {self.msg}'
        return f'{self.id}: {self.msg}'

    def getId(self) -> str:
        """Return unique message identifier."""
        return self.id

    def junit(self) -> TestCase:
        """
        Return JUnit XML test case.

        :returns: test case.
        """
        tc = TestCase(self.id, stdout=self.msg, file=self.filename, line=self.row)
        return tc


class UniventionPackageCheckBase:
    """Abstract base class for checks."""

    def __init__(self) -> None:
        self.name: str = self.__class__.__module__
        self.msg: List[UPCMessage] = []
        self.debuglevel: int = 0
        self.overrides = set()
        self.path = '.'  # base directory of Debian package to check.

    def addmsg(self, msgid: str, msg: str, filename: str | None = None, row: int | None = None, col: int | None = None, line: str = '') -> None:
        """
        Add :py:class:`UPCMessage` message.

        :param msgid: Message identifier.
        :param msg: Message text.
        :param filename: Associated file name.
        :param row: Associated line number.
        :param col: Associated column number.
        :param line: The line content itself (used for per-line ignores).
        """
        if line and noqa(line)(msgid):
            return
        message = UPCMessage(msgid, msg, filename, row, col)
        self.msg.append(message)

    def getMsgIds(self) -> MsgIds:
        """Return mapping from message-identifier to 2-tuple (severity, message-text)."""
        return {}

    def setdebug(self, level: int) -> None:
        """
        Set debug level.

        :param level: Debug level.
        """
        self.debuglevel = level

    def debug(self, msg: str) -> None:
        """
        Print debug message.

        :param msg: Text string.
        """
        if self.debuglevel > 0:
            print(f'{self.name}: {msg}')

    def postinit(self, path: str) -> None:
        """
        Checks to be run before real check or to create precalculated data for several runs. Only called once!

        :param path: Directory or file to check.
        """

    def main(self, pathes: List[str]) -> None:
        """
        The real check.

        :param pathes: files to check.
        """

    def check(self, path: str) -> None:
        """
        The real check.

        :param path: Directory or file to check.
        """
        self.path = path

    def result(self) -> List[UPCMessage]:
        """
        Return result as list of messages.

        :returns: List of :py:class:`UPCMessage`
        """
        return self.msg

    @classmethod
    def run(cls, arguments=None):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-o', '--display-only', metavar='MODULES',
            dest='display_only_IDs', action='append', default=[],
            help='list of IDs to be displayed (e.g. -o 9-1,0027-12)',
        )
        parser.add_argument(
            '-i', '--ignore', metavar='MODULES',
            dest='ignore_IDs', action='append', default=[],
            help='list of IDs to be ignored (e.g. -i 0003-4,19-27)',
        )
        parser.add_argument(
            '-d', '--debug', metavar='LEVEL',
            type=int, default=0,
            help='if set, debugging is activated and set to the specified level',
        )
        parser.add_argument(
            '-c', '--display-categories', metavar='CATEGORIES',
            dest='display_only_categories', default='',
            help='categories to be displayed (e.g. -c EWIS)',
        )
        parser.add_argument(
            '-e', '--exitcode-categories', metavar='CATEGORIES',
            default='E',
            help='categories that cause an exitcode != 0 (e.g. -e EWIS)',
        )
        parser.add_argument('files', nargs='*')
        args = parser.parse_args(arguments)

        for path in args.files:
            print(os.getpid(), path, file=sys.stderr)

        ignore_IDs = [clean_id(x) for ign in args.ignore_IDs for x in ign.split(',')]
        display_only_IDs = [clean_id(x) for dsp in args.display_only_IDs for x in dsp.split(',')]
        fail = False
        for base, files in cls.group_by_package(args.files):
            msglist = []  # type: List[UPCMessage]
            obj = cls()
            obj.path = base
            obj.setdebug(args.debug)
            obj.postinit(obj.path)
            try:
                obj.main(files)
            except UCSLintException as ex:
                print(ex, file=sys.stderr)
            msglist.extend(obj.result())
            incident_cnt, exitcode_cnt = obj.printResult(msglist, ignore_IDs, display_only_IDs, args.display_only_categories, args.exitcode_categories)
            fail |= bool(exitcode_cnt)

        return 2 if fail else 0

    @classmethod
    def group_by_package(cls, files):
        packages = {}
        for filename in files:
            parent_dir = os.path.dirname(filename)
            while not os.path.isdir(os.path.join(parent_dir, 'debian')) and parent_dir != '/':
                parent_dir = os.path.abspath(os.path.join(parent_dir, os.path.pardir))
            packages.setdefault(parent_dir, []).append(filename)
        return packages.items()

    def loadOverrides(self) -> None:
        """Parse :file:`debian/ucslint.overrides` file."""
        self.overrides = set()
        fn = os.path.join(self.path, 'debian', 'ucslint.overrides')
        try:
            with open(fn) as overrides:
                for row, line in enumerate(overrides, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith('#'):
                        continue
                    result = RE_OVERRIDE.match(line)
                    if not result:
                        print('IGNORED: debian/ucslint.overrides:%d: %s' % (row, line), file=sys.stderr)
                        continue

                    module, pattern, linenumber = result.groups()
                    override = (module, pattern, int(linenumber) if pattern and linenumber else None)
                    self.overrides.add(override)
        except OSError as ex:
            if ex.errno != ENOENT:
                print('WARNING: load debian/ucslint.overrides: %s' % (ex,), file=sys.stderr)

    def in_overrides(self, msg: UPCMessage) -> bool:
        """
        Check message against overrides.

        :param msg: Message to check.
        :returns: `True` when the check should be ignored, `False` otherwise.
        """
        filepath = normpath(relpath(msg.filename, self.path)) if msg.filename else ''
        for (modulename, pattern, linenumber) in self.overrides:
            if modulename != msg.getId():
                continue
            if pattern and not fnmatch(filepath, pattern):
                continue
            if linenumber is not None and linenumber != msg.row:
                continue
            return True
        return False

    def printResult(
            self,
            msglist,
            ignore_IDs: List[str],
            display_only_IDs: List[str],
            display_only_categories: str,
            exitcode_categories: str,
            #junit: IO[str] = None
    ) -> Tuple[int, int]:
        """
        Print result of checks.

        :param ignore_IDs: List of message identifiers to ignore.
        :param display_only_IDs: List of message identifiers to display.
        :param display_only_categories: List of message categories to display.
        :param exitcode_categories: List of message categories to signal as fatal.
        :param junit: Generate JUnit XML output to given file.
        :returns: 2-tuple (incident-count, exitcode-count)
        """
        incident_cnt = 0
        exitcode_cnt = 0

        self.loadOverrides()
        test_cases = []  # type: List[TestCase]
        msgidlist = self.getMsgIds()

        for msg in msglist:
            tc = msg.junit()
            test_cases.append(tc)

            if msg.getId() in ignore_IDs:
                tc.add_skipped_info('ignored')
                continue
            if display_only_IDs and msg.getId() not in display_only_IDs:
                tc.add_skipped_info('hidden')
                continue
            if self.in_overrides(msg):
                # ignore msg if mentioned in overrides files
                tc.add_skipped_info('overridden')
                continue

            msgid = msg.getId()
            try:
                lvl, msgstr = msgidlist[msgid]
                category = RESULT_INT2STR[lvl]
            except LookupError:
                category = 'FIXME'

            if category in display_only_categories or display_only_categories == '':
                print('%s:%s' % (category, msg))
                incident_cnt += 1

            if category in exitcode_categories or exitcode_categories == '':
                exitcode_cnt += 1

        # if junit:
        #     ts = TestSuite("ucslint", test_cases)
        #     TestSuite.to_file(junit, [ts], prettyprint=False)

        return incident_cnt, exitcode_cnt


class UniventionPackageCheckDebian(UniventionPackageCheckBase):
    """Check for :file:`debian/` directory."""

    def check(self, path: str) -> None:
        """the real check."""
        super().check(path)
        if not os.path.isdir(os.path.join(path, 'debian')):
            raise UCSLintException(f"directory '{path}' does not exist!")


class UCSLintException(Exception):
    """Top level exception."""


class DebianControlNotEnoughSections(UCSLintException):
    """Content exception."""


class DebianControlParsingError(UCSLintException):
    """Parsing exception."""


class FailedToReadFile(UCSLintException):
    """File reading exception."""

    def __init__(self, fn: str) -> None:
        super().__init__()
        self.fn = fn


class DebianControlEntry(Dict[str, str]):
    """
    Handle paragraph in Deb822 control file.

    :param content: String content of paragraph.
    """

    RE_MULTILINE = re.compile(r'$\n\s', re.MULTILINE)

    def __init__(self, content: str) -> None:
        dict.__init__(self)

        content = self.RE_MULTILINE.sub(' ', content)
        for line in content.splitlines():
            try:
                key, val = line.split(':', 1)
            except ValueError:
                raise DebianControlParsingError(line)
            self[key.strip()] = val.strip()

    def _split_field(self, s: str) -> Iterator[str]:
        """Split control field into parts. Returns generator."""
        for con in s.split(','):
            con = con.strip()
            for dis in con.split('|'):
                i = dis.find('(')
                if i >= 0:
                    dis = dis[:i]

                pkg = dis.strip()
                if pkg:
                    yield pkg

    def _pkgs(self, key: str) -> Set[str]:
        """Return package list."""
        return set(self._split_field(self.get(key, "")))


class DebianControlSource(DebianControlEntry):
    """Source package entry from :file:`debian/control`."""

    dep = property(lambda self: self._pkgs('Build-Depends'))
    dep_indep = property(lambda self: self._pkgs('Build-Depends-Indep'))
    dep_arch = property(lambda self: self._pkgs('Build-Depends-Arch'))
    dep_all = property(lambda self: self.dep | self.dep_indep | self.dep_arch)
    conf = property(lambda self: self._pkgs('Build-Conflicts'))
    conf_indep = property(lambda self: self._pkgs('Build-Conflicts-Indep'))
    conf_arch = property(lambda self: self._pkgs('Build-Conflicts-Arch'))
    conf_all = property(lambda self: self.conf | self.conf_indep | self.conf_arch)


class DebianControlBinary(DebianControlEntry):
    """Binary package entry from :file:`debian/control`."""

    pre = property(lambda self: self._pkgs('Pre-Depends'))
    dep = property(lambda self: self._pkgs('Depends'))
    rec = property(lambda self: self._pkgs('Recommends'))
    sug = property(lambda self: self._pkgs('Suggests'))
    all = property(lambda self: self.pre | self.dep | self.rec | self.sug)
    bre = property(lambda self: self._pkgs('Breaks'))
    enh = property(lambda self: self._pkgs('Enhances'))
    repl = property(lambda self: self._pkgs('Replaces'))
    conf = property(lambda self: self._pkgs('Conflicts'))
    pro = property(lambda self: self._pkgs('Provides'))


class ParserDebianControl:
    """
    Parse :file:`debian/control` file.

    :param filename: Full path.
    """

    RE_COMMENT = re.compile(r'^#.*$\n?', re.MULTILINE)
    RE_SECTION = re.compile(r'\n{2,}', re.MULTILINE)

    def __init__(self, filename: str) -> None:
        self.filename = filename

        try:
            content = open(self.filename).read()
        except OSError:
            raise FailedToReadFile(self.filename)

        content = self.RE_COMMENT.sub('', content)

        parts = [part for part in self.RE_SECTION.split(content) if part]
        try:
            self.source_section = DebianControlSource(parts.pop(0))
            self.binary_sections = [DebianControlBinary(part) for part in parts]
        except IndexError:
            raise DebianControlNotEnoughSections()


class RegExTest:
    """
    Regular expression test.

    :param regex: Compiled regular expression.
    :param msgid: Message identifier.
    :param msg: Message text.
    :param cntmin: Required minimum number of matches.
    :param cntmax: Allowed maximum number of matches.
    """

    def __init__(self, regex: Pattern[str], msgid: str, msg: str, cntmin: int | None = None, cntmax: int | None = None) -> None:
        self.regex = regex
        self.msgid = msgid
        self.msg = msg
        self.cntmin = cntmin
        self.cntmax = cntmax
        self.cnt = 0


class UPCFileTester:
    """
    Univention Package Check - File Tester
    simple class to test if a certain text exists/does not exist in a textfile

    By default only the first 100k of the file will be read.

    Example::

        import re
        x = UPCFileTester()
        x.addTest(re.compile(r'ext[234]'), '5432-1', 'Habe ein extfs gefunden.', cntmax=0)
        x.addTest(re.compile(r'squashfs'), '1234-5', 'Habe kein squashfs gefunden.', cntmin=1)
        x.open('/etc/fstab')
        msglist = x.runTests()
        for msg in msglist:
            print('%s ==> %s ==> %s' % (msg.id, msg.filename, msg.msg))

        5432-1: /etc/fstab:4:29: Habe ein extfs gefunden.
        5432-1: /etc/fstab:7:19: Habe ein extfs gefunden.
        1234-5: /etc/fstab: Habe kein squashfs gefunden.
    """

    def __init__(self, maxsize: int = 100 * 1024) -> None:
        """
        creates a new :py:class:`UPCFileTester` object

        :param maxsize: maximum number of bytes read from specified file
        """
        self.maxsize = maxsize
        self.filename: str | None = None
        self.raw: str = ''
        self.lines: List[str] = []
        self.tests: List[RegExTest] = []

    def open(self, filename: str) -> None:
        """
        Opens the specified file and reads up to `maxsize` bytes into memory.

        :param filename: File to process.
        """
        self.filename = filename
        # hold raw file in memory (self.raw) and a unwrapped version (self.lines)
        # the raw version is required to calculate the correct position.
        # tests will be done with unwrapped version.
        try:
            self.raw = open(filename, 'r').read(self.maxsize)
        except UnicodeDecodeError:
            self.raw = ''
        lines = self.raw.replace('\\\n', '  ').replace('\\\r\n', '   ')
        self.lines = lines.splitlines()

    def _getpos(self, linenumber: int, pos_in_line: int) -> Tuple[int, int]:
        """
        Converts 'unwrapped' position values (line and position in line) into
        position values corresponding to the raw file.
        Counting of lines and position starts at 1, so first byte is at line 1 pos 1!

        :param linenumber: Line number starting at 1.
        :param pos_in_line: Column number startin at 1.
        :returns: 2-tuple (line-number, column-number).
        """
        pos = sum(len(_) + 1 for _ in self.lines[:linenumber])
        pos += pos_in_line
        raw = self.raw[:pos]
        realpos = len(raw) - raw.rfind('\n')
        realline = raw.count('\n')
        return (realline + 1, realpos)

    def addTest(self, regex: Pattern[str], msgid: str, msg: str, cntmin: int | None = None, cntmax: int | None = None) -> None:
        """
        add a new test

        :param regex: Compiled regular expression pattern.
        :param msgid: msgid for :py:class:`UPCMessage`.
        :param msg: message for :py:class:`UPCMessage`.
        :param cntmin: 'regex' has to match at least 'cntmin' times otherwise a :py:class:`UPCMessage` will be added.
        :param cntmax: 'regex' has to match at most 'cntmax' times otherwise a :py:class:`UPCMessage` will be added.

        :raises ValueError: if neither `cntmin` nor `cntmax` has been set
        """
        if cntmin is None and cntmax is None:
            raise ValueError('cntmin or cntmax has to be set')
        self.tests.append(RegExTest(regex, msgid, msg, cntmin, cntmax))

    def runTests(self) -> List[UPCMessage]:
        """
        Runs all given tests on loaded file.

        :returns: a list of :py:class:`UPCMessage` objects
        """
        if not self.filename:
            raise Exception('no file has been loaded')

        msglist = []
        for t in self.tests:
            t.cnt = 0

        for row, line in enumerate(self.lines):
            ignore = noqa(line)
            for t in self.tests:
                if ignore(t.msgid):
                    continue

                match = t.regex.search(line)
                if not match:
                    continue

                t.cnt += 1
                if t.cntmax is None or t.cnt <= t.cntmax:
                    continue

                # a maximum counter has been defined and maximum has been exceeded
                start, end = match.span()
                startline, startpos = self._getpos(row, start)
                msg = '{}\n\t{}\n\t{}{}'.format(
                    t.msg,
                    line.expandtabs(),
                    ' ' * len(line[:start].expandtabs()),
                    '^' * len(line[start:end].expandtabs()),
                )
                msglist.append(UPCMessage(t.msgid, msg, self.filename, startline, startpos))

        # check if mincnt has been reached by counter - if not then add UPCMessage
        for t in self.tests:
            if t.cntmin is not None and t.cnt < t.cntmin:
                msglist.append(UPCMessage(t.msgid, t.msg, self.filename))

        return msglist


class FilteredDirWalkGenerator:

    IGNORE_DIRS = {
        'CVS',
        '.git',
        '.mypy_cache',
        '.pybuild',
        '__pycache__',
        '.svn',
    }
    IGNORE_SUFFIXES = {
        '~',
        '.bak',
        '.pyc',
        '.pyo',
        '.swp',
    }
    IGNORE_FILES = {
        'config.guess',
        'configure',
        'libtool',
        'depcomp',
        'install-sh',
        'config.sub',
        'missing',
        'config.status',
    }
    BINARY_SUFFIXES = {
        '.ai',  # Adobe Illustrator
        '.bz2',
        '.cer',  # certificate
        '.class',  # Java Class
        '.cvd',  # ClamAV Virus Database
        '.deb',  # Debian package
        '.der',  # certificate
        '.dll',  # shared library
        '.efi.signed',  # Extensible Firmware Interface
        '.gd2',  # LibGD2 image
        '.gif',  # Graphics Interchange Format
        '.gpg',  # GNU Privacy Guard
        '.gz',
        '.ico',  # Windows Icon
        '.jar',  # Java Archive
        '.jpeg',  # Joint Photographic Experts Group
        '.jpg',  # Joint Photographic Experts Group
        '.mo',  # Gnutext Message object
        '.pdf',  # Portable Document Format
        '.png',  # Portable Network Graphics
        '.so',  # shared library
        '.svg',  # Scalable Vector Graphics
        '.svgz',  # Scalable Vector Graphics
        '.swf',  # Shockwave Flash
        '.ttf',  # True Type Font
        '.udeb',  # Debian package
        '.woff',  # Web Open Font
        '.xcf',  # GIMP
        '.xz',
        '.zip',
    }
    DOCUMENTATION_SUFFIXES = {
        '.1',
        '.2',
        '.3',
        '.4',
        '.5',
        '.6',
        '.7',
        '.8',
        '.doc',
        '.html',
        '.md',
        '.po',
        '.rst',
        '.txt',
        '.xml',
        'changelog',
        'ChangeLog',
        'README',
    }

    def __init__(
            self,
            path: str,
            ignore_dirs: Iterable[str] | None = None,
            prefixes: Iterable[str] | None = None,
            suffixes: Iterable[str] | None = None,
            ignore_suffixes: Iterable[str] | None = None,
            ignore_files: Iterable[str] | None = None,
            ignore_debian_subdirs: bool = True,
            reHashBang: Pattern[str] | None = None,
            readSize: int = 2048,
            dangling_symlinks: bool = False,
    ) -> None:
        """
        FilteredDirWalkGenerator is a generator that walks down all directories and returns all matching filenames.

        There are several possibilities to limit returned results:

        :param ignore_dirs: a list of additional directory names that will be excluded when traversing subdirectories (e.g. `['.git', '.svn']`)
        :param prefixes: a list of prefixes files have to start with (e.g. `['univention-', 'preinst']`)
        :param suffixes: a list of suffixes files have to end with (e.g. `['.py', '.sh', '.patch']`)
        :param ignore_suffixes: a list of additional files, that end with one of defined suffixes, will be ignored (e.g. `['~', '.bak']`)
        :param ignore_files: list of additional files that will be ignored (e.g. `['.gitignore', 'config.sub']`).
        :param ignore_debian_subdirs: boolean that defines if :file:`.../debian/*` directories are ignored or not.
        :param reHashBang: if defined, additionally text files are returned whose first characters match specified regular expression.
        :param readSize: number of bytes that will be read for e.g. reHashBang

        example::

             for fn in FilteredDirWalkGenerator(path, suffixes=['.py']):
               print(fn)
        """
        self.path = path
        self.ignore_dirs = set(ignore_dirs or ()) | self.IGNORE_DIRS
        self.prefixes = prefixes
        self.suffixes = suffixes
        self.ignore_suffixes = set(ignore_suffixes or ()) | self.IGNORE_SUFFIXES
        self.ignore_files = set(ignore_files or ()) | self.IGNORE_FILES
        self.ignore_debian_subdirs = ignore_debian_subdirs
        self.reHashBang = reHashBang
        self.readSize = readSize
        self.dangling_symlinks = dangling_symlinks

    def __iter__(self) -> Iterator[str]:
        for dirpath, dirnames, filenames in os.walk(self.path):
            # remove undesired directories
            if self.ignore_dirs:
                for item in self.ignore_dirs:
                    if item in dirnames:
                        dirnames.remove(item)

            # ignore all subdirectories in debian directory if requested
            if self.ignore_debian_subdirs and os.path.basename(dirpath) == 'debian':
                del dirnames[:]

            # iterate over filenames
            for filename in filenames:
                fn = os.path.join(dirpath, filename)

                # skip danling symlinks by default
                if not os.path.exists(fn) and not self.dangling_symlinks:
                    continue

                # check if filename is on ignore list
                if self.ignore_files and filename in self.ignore_files:
                    continue

                # check if filename ends with ignoresuffix
                if self.ignore_suffixes and any(fn.endswith(suffix) for suffix in self.ignore_suffixes):
                    continue

                # check if filename starts with required prefix
                if self.prefixes and not any(filename.startswith(prefix) for prefix in self.prefixes):
                    continue

                # check if filename ends with required suffix
                if self.suffixes and any(filename.endswith(suffix) for suffix in self.suffixes):
                    pass
                elif self.reHashBang:
                    try:
                        content = open(fn).read(self.readSize)
                    except (OSError, UnicodeDecodeError):
                        continue
                    if not self.reHashBang.search(content):
                        continue
                elif self.suffixes:
                    continue

                # return complete filename
                yield fn


if __name__ == '__main__':
    import doctest
    doctest.testmod()
