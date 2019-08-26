from mo_dots import wrap
from mo_testing.fuzzytestcase import FuzzyTestCase

from measure_noise import deviance
from tests import DATA, plot


class TestBasic(FuzzyTestCase):

    def test_distracting_point(self):
        raw_data = wrap([
            333.5, 322.5, 316.5, 326, 321, 330, 345.5,
            668.5,  # THIS POINT MESSES WITH DETECTION
            342, 319.5,
            323.5, 320.5, 328, 340.5, 339, 322, 350.5, 284.5, 331, 362,
            323.5, 323, 317.5, 338,
            # DISCONTINUITY
            454, 751.5, 715, 731.5, 443, 425, 729.5, 709, 739.5, 733.5, 791, 720.5,
            21038, 21046  # THESE POINTS DO NOT HELP
        ])

        data = raw_data.left(24)
        plot(data)
        description, scale = deviance(data)
        self.assertEqual(description, "OK")

        data = raw_data.right(14).left(12)
        plot(data)
        description, scale = deviance(data)
        self.assertEqual(description, "OK")

    def test_imbalance(self):
        data = DATA.imbalance.right(120)
        plot(data)
        description, score = deviance(data)
        self.assertEqual(description, "SKEWED")

    def test_bimodal(self):
        data = DATA.bimodal.right(120)
        plot(data)
        description, score = deviance(data)
        self.assertEqual(description, "MODAL")

    def test_normal_and_small(self):
        data = DATA.normal_and_small.right(150).left(100)
        plot(data)
        description, score = deviance(data)
        self.assertEqual(description, "OK")

        data = DATA.normal_and_small.right(49)
        plot(data)
        description, score = deviance(data)
        self.assertEqual(description, "SKEWED")

    def test_normal(self):
        data = DATA.normal.left(200)
        plot(data)
        description, score = deviance(data)
        self.assertEqual(description, "OK")

        data = DATA.normal_and_small.right(49)
        plot(data)
        description, score = deviance(data)
        self.assertEqual(description, "SKEWED")

    def test_one_bad_point(self):
        data = DATA.one_bad_point.right(160)
        plot(data)
        description, score = deviance(data)
        self.assertEqual(description, "OK")







