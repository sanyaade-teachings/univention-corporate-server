#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import json
from itertools import groupby
from operator import itemgetter


try:
    from typing import Dict, Iterable, List, Tuple  # noqa: F401
except ImportError:
    pass


# from ../conftest.py
MAJOR, MINOR, PATCH = RELEASE = (3, 0, 1)
ERRAT = 3
ARCH = 'amd64'
DATA = b'x' * 100  # univention.updater.tools.MIN_GZIP
RJSON = '/ucs-releases.json'


def gen_releases(releases=[], major=MAJOR, minor=MINOR, patches=range(PATCH + 1)):  # type: (Iterable[Tuple[int, int, int]], int, int, Iterable[int]) -> bytes
    """
    Generate a `ucs-releases.json` string from a list of given releases.

    :param releases: List of UCS releases.
    :param major: UCS major version.
    :param minor: UCS minor version.
    :param patches: List of UCS patch-level versions.

    >>> gen_releases([(MAJOR, MINOR, 0), (MAJOR, MINOR, 1)]) == gen_releases(patches=[0, 1])
    True
    """
    releases = list(releases) or [(major, minor, patch) for patch in patches]
    data = {
        "releases": [
            {
                "major": major,
                "minors": [
                    {
                        "minor": minor,
                        "patchlevels": [
                            {
                                "patchlevel": patchlevel,
                                "status": "maintained",
                            } for major, minor, patchlevel in patchelevels  # noqa: F812
                        ],
                    } for minor, patchelevels in groupby(minors, key=itemgetter(1))  # noqa: F812
                ],
            } for major, minors in groupby(releases, key=itemgetter(0))  # noqa: F812
        ],
    }
    return json.dumps(data).encode('UTF-8')
