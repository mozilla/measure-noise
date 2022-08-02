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

from unittest import TestCase

from jx_python import jx
from mo_logs import Log
import numpy

from measure_noise import deviance


class TestNormal(TestCase):
    def test_normal(self):
        num = 1000

        results = []
        for i in range(0, num):
            samples = numpy.random.normal(size=20)
            desc, score = deviance(samples)
            results.append(desc)

        self.assertEqual(list(jx.groupby(["ok", "not ok"])), [("not ok", ["not ok"]), ("ok", ["ok"])], "expecting version >=2.53")

        # normals ar OK
        for desc, n in jx.groupby(results):
            Log.note("{{desc}}: {{count}}", desc=desc, count=len(n))
            if desc == "OK":
                self.assertLessEqual(num * 0.99, len(n))

