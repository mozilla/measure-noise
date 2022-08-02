# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Perftest Team (perftest@mozilla.com)
#
from __future__ import absolute_import, division, unicode_literals

from jx_python import jx
from jx_python.containers.list import ListContainer
from mo_future import first
from mo_logs import Log
from pyLibrary.env import http

http.DEBUG = True


http.default_headers = {
    "User-Agent": "Python requests (https://github.com/mozilla/measure-noise)",
    "Referer": "https://github.com/mozilla/measure-noise",
}


def download_perfherder(desc, repo, id, dummy, framework):
    sig_result = http.get_json(
        "https://treeherder.mozilla.org/api/project/"
        + repo
        + "/performance/signatures/?format=json&framework="
        + str(framework)
        + "&id="
        + str(id)
    )

    signature = first(sig_result.keys())
    data_result = http.get_json(
        "https://treeherder.mozilla.org/api/project/"
        + repo
        + "/performance/data/?signatures="
        + signature
    )

    Log.note(
        "{{result|json}}",
        result={
            "name": desc,
            "data": jx.run({
                "from": ListContainer("data", data_result[signature]),
                "sort": "push_timestamp",
                "select": "value"
            }).data
        },
    )


download_perfherder(
    "Bimodal, imbalance in probability", "mozilla-central", 1937036, 1, 10
)
download_perfherder(
    "Example of normal noise before, good noise after", "mozilla-central", 1978280, 1, 10
)
download_perfherder("Bad", "mozilla-central", 1982073, 1, 10)
download_perfherder(
    "Breaks normality assumption (?multi-modal?)", "mozilla-central", 2092476, 1, 10
)
download_perfherder(
    'One bad point should not be considered "noise" (mean 3K)',
    "mozilla-central",
    2007143,
    1,
    10,
)
download_perfherder(
    "Mean=4K, about the same variance as above, is noise measure in absolute, or relative?",
    "mozilla-central",
    2007068,
    1,
    10,
)
download_perfherder("Are waves in the data noise?", "mozilla-central", 2008829, 1, 10)
download_perfherder("not-quite-balanced bimodal", "mozilla-central", 2007043, 1, 10)
