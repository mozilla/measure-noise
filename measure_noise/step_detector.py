import numpy as np
from scipy.stats import stats, rankdata

from measure_noise.utils import plot
from mo_collections import not_right, not_left
from mo_dots import Data, Null
from mo_math import ceiling

SHOW_CHARTS = True


MIN_POINTS = 6
MAX_POINTS = 24

operator_scale = 5
operator_radius = 30
forward = np.exp(-np.arange(operator_radius) / operator_scale) / operator_scale

# CHOICE OF edge_operator DEPENDS ON STD AND P_THRESHOLD
edge_operator = np.concatenate((-forward[::-1], forward))  # APPROX sign(x)*exp(-abs(x))
TOP_EDGES = 0.05  # NUMBER OF POINTS TO INVESTIGATE EDGES (PERCENT)
P_THRESHOLD = pow(10, -5)
JITTER = 20  # NUMBER OF SAMPLES (+/-) TO LOOK FOR BETTER EDGES

ABS = 1


def find_segments(values, diff_type, diff_threshold):
    values = np.array(values)
    logs = np.log(values)
    # EDGE DETECTION BASED ON VALUE
    # values = np.array(values)
    # plot(values)
    # extra = np.concatenate((
    #     np.repeat(values[0], filter_radius),
    #     values,
    #     np.repeat(values[-1], filter_radius)
    # ))/np.mean(values)
    #
    # edge_detection = np.convolve(extra, edge_filter, mode="valid")
    # plot(edge_detection)

    # EDGE DETECTION BASED ON RANK
    ranks = rankdata(values)
    SHOW_CHARTS and plot(ranks, title="RANKS")
    # ADD SOME EXTRA DATA TO EDGES TO MINIMIZE EDGE ARTIFACTS
    # CONVERT RANK TO PERCENTILE
    extra = (
        np.concatenate(
            (
                np.repeat(ranks[0], operator_radius),
                ranks,
                np.repeat(ranks[-1], operator_radius),
            )
        )
        - 1
    ) / len(values)
    edge_detection = np.convolve(extra, edge_operator, mode="valid")
    SHOW_CHARTS and plot(edge_detection, title="EDGES")
    top_edges = np.argsort(-np.abs(edge_detection))[: ceiling(len(values) * TOP_EDGES)]

    # SORT THE EDGE DETECTION
    segments = np.array([0, len(values)] + list(top_edges))
    segments = np.sort(segments)

    # CAN WE DO BETTER?
    for i, _ in enumerate(segments[:-2]):
        s, m, e = segments[i], segments[i + 1], segments[i + 2]
        m_score, t_score, best_mid = jitter_MWU(logs, s, m, e)
        if m_score.pvalue > P_THRESHOLD:
            # NO EVIDENCE OF DIFFERENCE, COLLAPSE SEGMENT
            segments[i + 1] = segments[i]
            continue
        elif t_score.pvalue > P_THRESHOLD:
            # NO EVIDENCE OF DIFFERENCE, COLLAPSE SEGMENT
            segments[i + 1] = segments[i]
            continue
        elif diff_type == ABS and np.abs(np.median(values[s:best_mid]) - np.median(values[best_mid:e])) < diff_threshold:
            # DIFFERENCE IS TOO SMALL
            segments[i + 1] = segments[i]
            continue
        elif np.abs(np.median(logs[s: best_mid]) - np.median(logs[best_mid: e])) < diff_threshold / 100:
            # DIFFERENCE IS TOO SMALL
            segments[i + 1] = segments[i]
            continue

        # LOOKS GOOD
        segments[i + 1] = best_mid

    segments = tuple(sorted(set(segments)))
    return segments


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

no_good=Data(pvalue=1)


def jitter_MWU(values, start, mid, end):
    # ADD SOME CONSTRAINTS TO THE RANGE OF VALUES TESTED
    m_start = min(mid, max(start + MIN_POINTS, mid - JITTER))
    m_end = max(mid, min(mid + JITTER, end - MIN_POINTS))
    if m_start == m_end:
        return no_good, no_good, mid
    mids = np.array(range(m_start, m_end))

    # MWU SCORES
    m_score = np.array(
        [
            stats.mannwhitneyu(
                values[start:m],
                values[m:end],
                use_continuity=True,
                alternative="two-sided",
            )
            for m in mids
        ]
    )

    t_score = np.array(
        [
            stats.ttest_ind(
                values[start:m],
                values[m:end],
                equal_var=False
            )
            for m in mids
        ]
    )

    # TOTAL SUM-OF-SQUARES
    v_prefix = not_right(not_left(cumSS(values[start:m_end]), m_start - start - 1), 1)
    v_suffix = not_right(cumSS(values[m_start:end][::-1])[::-1], end - m_end)
    v_score = v_prefix + v_suffix

    # PICK LOWEST
    pvalue = np.sqrt(m_score[:, 1] * v_score)  # GOEMEAN OF SCORES
    best = np.argmin(pvalue)

    return Data(pvalue=m_score[best, 1]), Data(pvalue=t_score[best, 1]), mids[best]
