import numpy
from unittest import TestCase

from measure_noise import deviance
from tests import perfherder_alert, plot


class TestPerfAlert(TestCase):

    def test_imbalance_false_negative(self):
        data = [
            333.5, 322.5, 316.5, 326, 321, 330, 345.5,
            668.5,  # THIS POINT MESSES WITH DETECTION
            342, 319.5,
            323.5, 320.5, 328, 340.5, 339, 322, 350.5, 284.5, 331, 362,
            323.5, 323, 317.5, 338,
            # DISCONTINUITY
            454, 751.5, 715, 731.5, 443, 425, 729.5, 709, 739.5, 733.5, 791, 720.5,
            21038, 21046  # THESE POINTS DO NOT HELP WITH DETECTION
        ]
        plot(data)
        result, changes = perfherder_alert(data)
        alert = any(changes)
        self.assertFalse(alert)  # The code should find this problem, but the outlier is causing a problem


    def test_alert(self):
        num_pre = 25
        num_post = 12
        num_resume = 2
        pre_samples = numpy.random.normal(loc=10, size=num_pre)
        post_samples = numpy.random.normal(loc=100, size=num_post - num_resume)
        resume_samples = numpy.random.normal(loc=10, size=num_resume)

        samples = list(pre_samples) + list(post_samples) + list(resume_samples)
        plot(samples)

        result, changes = perfherder_alert(samples)
        alert = any(changes)
        self.assertTrue(alert)

        desc, score = deviance(list(post_samples) + list(resume_samples))
        self.assertEqual("OUTLIERS", desc)
