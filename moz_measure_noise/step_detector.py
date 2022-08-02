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

import numpy as np
from numpy.lib.stride_tricks import as_strided
from scipy.stats import stats, rankdata

from moz_measure_noise.utils import plot
from mo_dots import Data, coalesce
from mo_logs import Except

SHOW_CHARTS = False


THRESHOLD = 4
P_THRESHOLD = pow(10, -THRESHOLD)
MIN_POINTS = 6
MAX_POINTS = 50
TOP_EDGES = 0.05  # NUMBER OF POINTS TO INVESTIGATE EDGES (PERCENT)
JITTER = 20  # NUMBER OF SAMPLES (+/-) TO LOOK FOR BETTER EDGES

weight_scale = 5
weight_length = 30
forward = np.exp(-np.arange(weight_length) / weight_scale) / weight_scale
median_weight = np.array(list(forward[::-1]) + list(forward))
weight_radius = len(median_weight) // 2

SHOW_CHARTS and plot(median_weight, title="WEIGHT")

PERFHERDER_THRESHOLD_TYPE_ABS = 1
DEFAULT_THRESHOLD = 0.03


def find_segments(values, diff_type, diff_threshold):
    values = list(values)
    if len(values) == 0:
        return (0,), (0,)
    diff_threshold = coalesce(diff_threshold, DEFAULT_THRESHOLD)

    values = logs = np.array(values)
    if np.all(values > 0):
        logs = np.log(values)
    ranks = rankdata(values)

    SHOW_CHARTS and plot(ranks/len(values), title="RANKS")
    mwus = sliding_MWU(values)
    edge_detection = -np.log10(mwus[:, 1])
    # edge_detection = np.convolve(percentiles, edge_wavelet, mode="valid")
    SHOW_CHARTS and plot(edge_detection, title="EDGES -log10(p_value)")
    top_edges = np.argsort(-edge_detection)
    top_edges = filter_nearby_edges(top_edges[edge_detection[top_edges] > THRESHOLD / 3])

    # SORT THE EDGE DETECTION
    segments = np.array([0, len(values)] + list(top_edges))
    segments = np.sort(segments)
    diffs = np.zeros(len(segments))

    # CAN WE DO BETTER?
    for i, _ in enumerate(segments[:-2]):
        s, m, e = segments[i], segments[i + 1], segments[i + 2]
        m_score, t_score, best_mid = jitter_MWU(logs, s, m, e)
        if m_score.pvalue > P_THRESHOLD or s == best_mid or e == best_mid:
            # NO EVIDENCE OF DIFFERENCE, COLLAPSE SEGMENT
            segments[i + 1] = s
            continue
        if diff_type == PERFHERDER_THRESHOLD_TYPE_ABS:
            diff_percent = np.abs(
                np.median(values[s:best_mid]) - np.median(values[best_mid:e])
            )
            if diff_percent < diff_threshold:
                # DIFFERENCE IS TOO SMALL
                segments[i + 1] = s
                continue
        diff_percent = np.abs(
            np.median(values[best_mid:e]) / np.median(values[s:best_mid]) - 1
        )

        try:
            too_small = diff_percent < diff_threshold / 100
        except Exception as cause:
            raise cause

        if too_small:
            # DIFFERENCE IS TOO SMALL
            segments[i + 1] = segments[i]
            continue

        # LOOKS GOOD
        segments[i + 1] = best_mid
        diffs[i + 1] = diff_percent

    # REMOVE ZERO-LENGTH SEGMENTS
    non_zero_segments = segments[:-1] != segments[1:]
    segments = tuple([0] + list(segments[1:][non_zero_segments]))
    diffs = tuple([0] + list(diffs[1:][non_zero_segments]))
    return segments, diffs


def filter_nearby_edges(edges):
    if len(edges) == 0:
        return edges
    filter_edges = edges[:1]
    for e in edges[1:]:
        if np.any((filter_edges - MIN_POINTS <= e) & (e <= filter_edges + MIN_POINTS)):
            continue
        filter_edges = np.append(filter_edges, [e])
    return filter_edges


def cumvar(values):
    m = np.arange(len(values))
    count = m + 1
    cummean = np.cumsum(values) / count
    cumvar = ((values - cummean) ** 2) / m
    return cumvar


def cumSS(values):
    """
    RETURN CUMULATIVE SUM-OF-SQUARES
    :param values:
    """
    m = np.arange(len(values))
    count = m + 1
    cummean = np.cumsum(values) / count
    return (values - cummean) ** 2


no_good_edge = Data(pvalue=1)


def jitter_MWU(values, start, mid, end):
    """
    RETURN A BETTER MIDPOINT< ACCOUNTING FOR t-test RESULTS
    """

    # ADD SOME CONSTRAINTS TO THE RANGE OF VALUES TESTED
    m_start = min(mid, max(start + MIN_POINTS, mid - JITTER))
    m_end = max(mid, min(mid + JITTER, end - MIN_POINTS))
    if m_start == m_end:
        return no_good_edge, no_good_edge, mid
    mids = np.array(range(m_start, m_end))

    # MWU SCORES
    try:
        m_score = np.array(
            [
                stats.mannwhitneyu(
                    values[max(start, m - MAX_POINTS) : m],
                    values[m : min(end, m + MAX_POINTS)],
                    use_continuity=True,
                    alternative="two-sided",
                )
                for m in mids
            ]
        )

        t_score = np.array(
            [
                stats.ttest_ind(
                    values[max(start, m - MAX_POINTS) : m],
                    values[m : min(end, m + MAX_POINTS)],
                    equal_var=False,
                )
                for m in mids
            ]
        )

    except Exception as e:
        e = Except.wrap(e)
        if "All numbers are identical" in e:
            return no_good_edge, no_good_edge, mids[0]
        raise e

    # TOTAL SUM-OF-SQUARES
    # DO NOT KNOW WHAT THIS WAS DOING
    # if m_start - start == 0:
    #     # WE CAN NOT OFFSET BY ONE, SO WE ADD A DUMMY VALUE
    #     v_prefix = np.array([np.nan] + list(not_right(cumSS(values[start:m_end]), 1)))
    # else:
    #     # OFFSET BY ONE, WE WANT cumSS OF ALL **PREVIOUS** VALUES
    #     v_prefix = not_right(
    #         not_left(cumSS(values[start:m_end]), m_start - start - 1), 1
    #     )
    # v_suffix = not_right(cumSS(values[m_start:end][::-1])[::-1], end - m_end)
    # v_score = v_prefix + v_suffix
    # pvalue = np.sqrt(m_score[:, 1] * v_score)  # GOEMEAN OF SCORES

    # PICK LOWEST
    pvalue = np.sqrt(m_score[:, 1]*t_score[:,1])
    best = np.argmin(pvalue)

    return Data(pvalue=m_score[best, 1]), Data(pvalue=t_score[best, 1]), mids[best]


def sliding_MWU(values):
    """
    RETURN
    :param values:
    :return:
    """
    # ADD MEDIAN TO EITHER SIDE OF values
    prefix = [np.median(values[: i + weight_radius]) for i in range(weight_radius)]
    suffix = [
        np.median(values[-i - weight_radius:])
        for i in reversed(range(weight_radius))
    ]
    combined = np.array(prefix + list(values) + suffix)
    b = combined.itemsize
    window = as_strided(
        combined, shape=(len(values), weight_radius * 2), strides=(b, b)
    )

    med = (len(median_weight) + 1) / 2
    try:
        m_score = np.array(
            [
                stats.mannwhitneyu(
                    w[:weight_radius],
                    w[-weight_radius:],
                    use_continuity=True,
                    alternative="two-sided",
                )
                for v in window
                for r in [rankdata(v)]
                for w in [(r - med) * median_weight]
            ]
        )

        return m_score
    except Exception as cause:
        cause = Except.wrap(cause)
        if "All numbers are identical" in cause:
            return np.ones((window.shape[0], 2))
        raise cause
