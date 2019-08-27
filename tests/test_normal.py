from __future__ import unicode_literals

from unittest import TestCase

from mo_logs import Log
import numpy

from jx_python import jx
from measure_noise import deviance
from tests import plot


class TestNormal(TestCase):
    def test_normal(self):
        num = 1000

        results = []
        for i in range(0, num):
            samples = numpy.random.normal(size=20)
            desc, score = deviance(samples)
            results.append(desc)

        # normals ar OK
        for desc, n in jx.groupby(results):
            Log.note("{{desc}}: {{count}}", desc=desc, count=len(n))
            if desc == "OK":
                self.assertLessEqual(num * 0.99, len(n))

