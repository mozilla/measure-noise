from __future__ import unicode_literals

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

        self.assertEqual(list(jx.groupby(["ok", "not ok"])), [("ok", ["ok"]), ("not ok", ["not ok"])], "expecting version >=2.53")

        # normals ar OK
        for desc, n in jx.groupby(results):
            Log.note("{{desc}}: {{count}}", desc=desc, count=len(n))
            if desc == "OK":
                self.assertLessEqual(num * 0.99, len(n))

