# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import absolute_import, division, unicode_literals

from unittest import TestCase

from measure_noise import deviance
from tests import plot


class TestBasic(TestCase):

    def test_distracting_point(self):
        data = [
            333.5, 322.5, 316.5, 326, 321, 330, 345.5, 668.5, 342, 319.5,
            323.5, 320.5, 328, 340.5, 339, 322, 350.5, 284.5, 331, 362,
            323.5, 323, 317.5, 338
        ]
        plot(data)
        description, scale = deviance(data)
        self.assertEqual(description, "OK")  # SINGLE-POINT ERRORS WILL NOT BE DETECTED

        data = [
            454, 751.5, 715, 731.5, 443, 425, 729.5, 709, 739.5, 733.5,
            791, 720.5
        ]
        plot(data)
        description, scale = deviance(data)
        self.assertEqual(description, "OK")

    def test_imbalance(self):
        data = [
            425, 430.5, 429, 422, 424.5, 436, 426.5, 425.5, 426, 781.5,
            427.5, 420, 431, 425.5, 784, 423.5, 421, 780.5, 427.5, 426,
            425, 423, 421.5, 424, 421.5, 425.5, 429.5, 425.5, 423.5, 426,
            430.5, 423.5, 787, 432, 432, 431, 427, 438.5, 426.5, 807.5,
            431, 450, 434, 427.5, 422.5, 432.5, 442, 427, 443, 439,
            434, 446, 431, 443.5, 432, 424, 434.5, 424, 431, 428.5,
            418, 430, 426.5, 428.5, 423, 422.5, 429.5, 425, 783.5, 429,
            432, 443, 427.5, 434.5, 427.5, 428.5, 419.5, 458.5, 426, 427.5,
            431, 431.5, 428, 428.5, 424, 427.5, 427.5, 419, 776, 414.5,
            420.5, 418, 423.5, 417.5, 419, 454, 416.5, 419, 418.5, 763.5,
            785.5, 418.5, 413, 418.5, 431, 425.5, 429, 419, 427.5, 428,
            429.5, 423.5, 430.5, 426, 423.5, 419, 795.5, 427.5, 422, 429.5
        ]
        plot(data)
        description, score = deviance(data)
        self.assertEqual(description, "OUTLIERS")

    def test_bimodal(self):
        data = [
            2178, 1288, 1211, 1265, 2361, 2275, 1197, 1241, 2317, 1309,
            2368, 1190, 1245, 2340, 1264, 2395, 2326, 2260, 2347, 1341,
            1202, 1367, 2283, 2419, 2411, 2291, 2289, 2269, 2321, 1246,
            1220, 1301, 2345, 2208, 2360, 2385, 1201, 2281, 1235, 1243,
            1265, 1262, 1273, 2342, 2259, 2312, 1192, 1391, 1259, 1226,
            1283, 2289, 1359, 1442, 2528, 2397, 2376, 2350, 1313, 2322,
            2291, 2241, 2273, 2291, 1231, 1220, 2272, 2328, 2418, 2435,
            1278, 2444, 2341, 2332, 2298, 2316, 2398, 1198, 2393, 1289,
            1241, 1170, 1336, 1255, 2360, 2287, 1240, 2260, 1323, 1231,
            1272, 1183, 2285, 2258, 2307, 2307, 2165, 2406, 2295, 1234,
            1189, 1186, 2320, 2312, 2400, 2321, 1170, 2318, 1209, 1270,
            2374, 2299, 1206, 1225, 2329, 2324, 1248, 2346, 2285, 2247
        ]
        plot(data)
        description, score = deviance(data)
        self.assertEqual(description, "MODAL")

    def test_normal_and_small(self):
        data = [
            593, 543.5, 660.5, 612, 549.5, 561, 456, 387.5, 451.5, 390,
            424.5, 490, 446, 504, 470.5, 417.5, 517, 806.5, 413.5, 625,
            494.5, 479.5, 421, 467, 432.5, 537, 472, 618, 372.5, 474.5,
            479.5, 413.5, 442.5, 666, 453, 441, 454.5, 464, 589, 435.5,
            392.5, 265.5, 471, 266, 631.5, 422.5, 389.5, 430.5, 418, 441,
            364, 269, 394, 589, 254.5, 427, 397.5, 398, 454, 461.5,
            428.5, 393.5, 458, 466, 271, 479, 392.5, 385.5, 399.5, 450,
            388, 468, 486, 381, 399, 389, 417, 473.5, 514, 268.5,
            453, 452.5, 390, 271, 271, 403, 462.5, 405, 403, 415.5,
            388, 264, 492.5, 435, 471.5, 457, 494, 427, 433, 431
        ]
        plot(data)
        description, score = deviance(data)
        self.assertEqual(description, "OK")

        data = [
            379.5, 381, 381.5, 370, 371.5, 367, 368.5, 372.5, 258, 361.5,
            373, 260, 365.5, 366.5, 366.5, 366.5, 369.5, 366.5, 359.5, 357.5,
            365, 363.5, 359.5, 360.5, 264.5, 360.5, 357.5, 370, 372, 376.5,
            363, 362, 263, 355.5, 368.5, 374, 265, 328.5, 359.5, 369,
            368.5, 361.5, 369, 370.5, 364.5, 365, 339.5, 257, 372
        ]
        plot(data)
        description, score = deviance(data)
        self.assertEqual(description, "SKEWED")

    def test_normal(self):
        data = [
            229.5, 244, 226.5, 245, 234.5, 228, 231.5, 242, 250.5, 237.5,
            227, 245, 226.5, 238, 231.5, 233.5, 231.5, 230, 231, 242.5,
            242, 239.5, 243.5, 234, 233.5, 241.5, 241.5, 236.5, 243, 240.5,
            241, 247, 253, 244, 241.5, 226, 223.5, 221.5, 238.5, 234.5,
            242, 223.5, 220.5, 230, 235.5, 227.5, 241, 232.5, 239.5, 228.5,
            234.5, 238.5, 246, 228.5, 263.5, 244, 229.5, 249, 234.5, 248,
            231.5, 225.5, 247.5, 250, 249.5, 242, 228.5, 232.5, 229.5, 242,
            244, 203.5, 246, 240.5, 239, 245, 238.5, 244.5, 244, 251.5,
            241.5, 248.5, 239.5, 237, 234.5, 244, 224.5, 240, 238, 248,
            229, 243, 250, 230.5, 240, 244.5, 229, 248, 237.5, 241,
            232, 247.5, 236, 234, 242, 241.5, 245.5, 235.5, 242, 234,
            248.5, 249.5, 230.5, 227, 238, 246, 225, 243.5, 226.5, 233.5,
            235.5, 228, 244.5, 228, 241.5, 237.5, 240, 244, 237, 246,
            239.5, 238.5, 244, 238.5, 248, 245.5, 247, 244, 253.5, 245.5,
            256, 242.5, 248.5, 250, 246.5, 249.5, 234, 250, 252, 250,
            243, 236, 237.5, 252.5, 245, 248, 230, 246, 250.5, 247,
            246, 255, 240, 246.5, 240, 233.5, 233.5, 244, 239, 247.5,
            241, 241, 237, 240.5, 239.5, 227.5, 242.5, 248, 230.5, 248,
            229.5, 239.5, 248.5, 237.5, 244.5, 253, 236, 239.5, 245, 228,
            249, 246, 235, 234, 241, 240, 237.5, 245, 242.5, 249
        ]
        plot(data)
        description, score = deviance(data)
        self.assertEqual(description, "OK")

        data = [
            379.5, 381, 381.5, 370, 371.5, 367, 368.5, 372.5, 258, 361.5,
            373, 260, 365.5, 366.5, 366.5, 366.5, 369.5, 366.5, 359.5, 357.5,
            365, 363.5, 359.5, 360.5, 264.5, 360.5, 357.5, 370, 372, 376.5,
            363, 362, 263, 355.5, 368.5, 374, 265, 328.5, 359.5, 369,
            368.5, 361.5, 369, 370.5, 364.5, 365, 339.5, 257, 372
        ]
        plot(data)
        description, score = deviance(data)
        self.assertEqual(description, "SKEWED")

    def test_one_bad_point(self):
        data = [
            3117, 3215, 3219, 3174, 3011, 3017, 2984, 3075, 3248, 3120,
            3158, 2994, 3224, 3105, 3131, 3141, 3033, 2986, 3184, 3235,
            3190, 3100, 3359, 3098, 3279, 3165, 3270, 3213, 3223, 3079,
            3157, 3256, 3090, 2984, 3131, 3029, 3121, 3006, 3278, 3043,
            3042, 2963, 2974, 3401, 3226, 3307, 3092, 3156, 3291, 3030,
            3162, 3154, 3072, 3265, 3284, 3182, 2985, 2967, 3191, 3278,
            3210, 3234, 3037, 3189, 3046, 2992, 2994, 3249, 3150, 3126,
            3068, 3185, 3249, 3209, 3257, 2964, 3199, 3320, 3070, 3261,
            3171, 3240, 3136, 3017, 3167, 3043, 3278, 3047, 3272, 8104,
            3103, 3163, 3200, 3233, 3162, 3366, 3213, 3047, 3018, 3042,
            3138, 3065, 3235, 3370, 3020, 3120, 3201, 3008, 3084, 3259,
            3073, 3271, 3036, 3306, 2998, 3260, 3187, 3079, 3146, 3007,
            3196, 3126, 3097, 3074, 3323, 3169, 3223, 3216, 3238, 3034,
            3255, 3083, 3208, 3071, 3243, 3192, 3284, 3241, 3190, 3062,
            3376, 3277, 3222, 3313, 3036, 3113, 3155, 3129, 3065, 3229,
            2969, 3016, 3116, 3015, 3204, 3000, 3318, 3125, 3329, 3055
        ]
        plot(data)
        description, score = deviance(data)
        self.assertEqual(description, "OK")
