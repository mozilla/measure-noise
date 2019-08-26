from math import sqrt

from mo_logs import Log
from numpy import mean, var, log
from scipy.stats import kurtosis, skew
from numpy import stack

DEBUG = True
PROBLEM_THRESHOLD = 3.0  # NUMBER OF STANDRAD DEVIATIONS BEFORE A PROBLEM IS HIGHLIGHTED


def moments(samples):
    data = stack(samples)
    return (len(data), mean(data), sqrt(var(data)), skew(data), kurtosis(data))


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
        Log.note(
            "skew={{skew}}  kurt={{kurt}}", skew=skew_normalized, kurt=kurt_normalized
        )

    if abs(skew_normalized) > PROBLEM_THRESHOLD:
        return "SKEWED", skew_normalized
    if abs(kurt_normalized) > PROBLEM_THRESHOLD:
        if kurt < 0:
            return "MODAL", kurt_normalized
        else:
            return "OUTLIERS", kurt_normalized

    return "OK", 0
