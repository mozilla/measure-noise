import numpy as np
from scipy.stats import stats, rankdata

from measure_noise.utils import plot
from mo_collections import not_right, not_left
from mo_dots import Data, Null
from mo_math import ceiling

SHOW_CHARTS = False


P_THRESHOLD = pow(10, -5)
MIN_POINTS = 6
MAX_POINTS = 50
TOP_EDGES = 0.05  # NUMBER OF POINTS TO INVESTIGATE EDGES (PERCENT)
JITTER = 20  # NUMBER OF SAMPLES (+/-) TO LOOK FOR BETTER EDGES

operator_scale = 5
operator_length = 30
forward = np.exp(-np.arange(operator_length) / operator_scale) / operator_scale
edge_operator = np.concatenate(
    (
        -forward[::-1],  # exp(x)
        [0] * MIN_POINTS,  # ZERO IN THE MIDDLE?
        forward,  # exp(-x)
    )
)
operator_radius = len(edge_operator) // 2

PERFHERDER_THRESHOLD_TYPE_ABS = 1


def find_segments(values, diff_type, diff_threshold):
    if len(values) == 0:
        return (0,), (0,)

    values = np.array(values)
    logs = np.log(values)
    ranks = rankdata(values)

    # ADD SOME EXTRA DATA TO EDGES TO MINIMIZE EDGE ARTIFACTS
    # CONVERT RANK TO PERCENTILE
    percentiles = (
        np.concatenate(
            (
                np.repeat(ranks[0], operator_radius),
                ranks,
                np.repeat(ranks[-1], operator_radius),
            )
        )
        - 1
    ) / len(values)
    SHOW_CHARTS and plot(percentiles[operator_radius:-operator_radius], title="RANKS")
    edge_detection = np.convolve(percentiles, edge_operator, mode="valid")
    SHOW_CHARTS and plot(edge_detection, title="EDGES")
    top_edges = np.argsort(-np.abs(edge_detection))[: ceiling(len(values) * TOP_EDGES)]
    top_edges = filter_nearby_edges(top_edges)

    # SORT THE EDGE DETECTION
    segments = np.array([0, len(values)] + list(top_edges))
    segments = np.sort(segments)
    diffs = [0] * len(segments)

    # CAN WE DO BETTER?
    for i, _ in enumerate(segments[:-2]):
        s, m, e = segments[i], segments[i + 1], segments[i + 2]
        m_score, t_score, best_mid = jitter_MWU(logs, s, m, e)
        if m_score.pvalue > P_THRESHOLD:
            # NO EVIDENCE OF DIFFERENCE, COLLAPSE SEGMENT
            segments[i + 1] = segments[i]
            continue
        if t_score.pvalue > P_THRESHOLD:
            # NO EVIDENCE OF DIFFERENCE, COLLAPSE SEGMENT
            segments[i + 1] = segments[i]
            continue
        if diff_type == PERFHERDER_THRESHOLD_TYPE_ABS:
            diff = np.abs(np.median(values[s:best_mid]) - np.median(values[best_mid:e]))
            if diff <diff_threshold:
                # DIFFERENCE IS TOO SMALL
                segments[i + 1] = segments[i]
                continue
        diff = np.abs(np.median(logs[best_mid:e])/np.median(logs[s:best_mid]) - 1)

        if diff < diff_threshold / 100:
            # DIFFERENCE IS TOO SMALL
            segments[i + 1] = segments[i]
            continue

        # LOOKS GOOD
        segments[i + 1] = best_mid
        diffs[i + 1] = diff

    segments, diffs = zip(*([(0, 0)]+[
        (e, d)
        for s, e, d in zip(segments, segments[1:], diffs[1:])
        if s != e
    ]))
    return segments, diffs


def filter_nearby_edges(edges):
    last = edges[0]
    filter_edges = [last]
    for e in edges[1:]:
        if e - MIN_POINTS <= last <= e + MIN_POINTS:
            continue
        filter_edges.append(e)
        last = e
    return np.array(filter_edges)


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
    # ADD SOME CONSTRAINTS TO THE RANGE OF VALUES TESTED
    m_start = min(mid, max(start + MIN_POINTS, mid - JITTER))
    m_end = max(mid, min(mid + JITTER, end - MIN_POINTS))
    if m_start == m_end:
        return no_good_edge, no_good_edge, mid
    mids = np.array(range(m_start, m_end))

    # MWU SCORES
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

    # TOTAL SUM-OF-SQUARES
    if m_start - start == 0:
        # WE CAN NOT OFFSET BY ONE, SO WE ADD A DUMMY VALUE
        v_prefix = np.array([np.nan] + list(not_right(cumSS(values[start:m_end]), 1)))
    else:
        # OFFSET BY ONE, WE WANT cumSS OF ALL **PREVIOUS** VALUES
        v_prefix = not_right(
            not_left(cumSS(values[start:m_end]), m_start - start - 1), 1
        )
    v_suffix = not_right(cumSS(values[m_start:end][::-1])[::-1], end - m_end)
    v_score = v_prefix + v_suffix

    # PICK LOWEST
    pvalue = np.sqrt(m_score[:, 1] * v_score)  # GOEMEAN OF SCORES
    best = np.argmin(pvalue)

    return Data(pvalue=m_score[best, 1]), Data(pvalue=t_score[best, 1]), mids[best]
