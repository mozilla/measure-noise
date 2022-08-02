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

from math import sqrt

from numpy import log, mean, array, std
from scipy.stats import kurtosis, skew

DEBUG = False
PROBLEM_THRESHOLD = 3  # NUMBER OF STANDARD DEVIATIONS BEFORE A PROBLEM IS HIGHLIGHTED


def moments(samples):
    data = array(samples)
    return len(data), mean(data), std(data), skew(data), kurtosis(data)


def identity(v):
    return v


def deviance(samples):
    """
    Measure the deviant noise: The amount the `samples` deviate from a normal distribution

    :param samples: Some list of floats with uni-variate data
    :return: (description, score) pair describing the problem, and how bad it is

    Description is one of:
    SKEWED - samples are heavily to one side of the mean
    OUTLIERS - there are more outliers than would be expected from normal distribution
    MODAL - few samples are near the mean (probably bimodal)
    N/A - not enough data to even guess
    OK - no egregious deviation from normal
    """

    if len(samples) < 6:
        return "N/A", 0

    if all(v > 0 for v in samples):
        # Use log(): We assume this is log-normal data
        transform = log
    else:
        transform = identity

    samples = sorted(samples)[1:-1]
    corrected_samples = transform(samples)
    (count, mean, stddev, skew, kurt) = moments(corrected_samples)

    # https://en.wikipedia.org/wiki/D%27Agostino%27s_K-squared_test

    skew_stddev = sqrt(6 * (count - 2) / ((count + 1) * (count + 3)))
    kurt_stddev = sqrt(
        24
        * count
        * (count - 2)
        * (count - 3)
        / ((count + 1) * (count + 1) * (count + 3) * (count + 5))
    )

    skew_normalized = skew / skew_stddev
    kurt_normalized = kurt / kurt_stddev

    if DEBUG:
        from mo_logs import Log

        Log.note(
            "skew={{skew}}  kurt={{kurt}}", skew=skew_normalized, kurt=kurt_normalized
        )

    # REPORT THE WORST NUMBER
    if abs(skew_normalized) > abs(kurt_normalized):
        if abs(skew_normalized) > PROBLEM_THRESHOLD:
            return "SKEWED", skew_normalized
        else:
            return "OK", skew_normalized
    else:
        if kurt_normalized > PROBLEM_THRESHOLD:
            return "OUTLIERS", kurt_normalized
        elif kurt_normalized < -PROBLEM_THRESHOLD:
            return "MODAL", kurt_normalized
        else:
            return "OK", kurt_normalized
