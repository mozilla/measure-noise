from math import sqrt

from numpy import mean, var
from scipy.stats import kurtosis, skew
from numpy import stack

def moments(samples):
    data = stack(samples)
    return (
        len(data),
        mean(data),
        sqrt(var(data)),
        skew(data),
        kurtosis(data)
    )
