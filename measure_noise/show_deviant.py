from time import sleep

import numpy as np
import plotly.graph_objects as go
from scipy.stats import stats, rankdata

from jx_python import jx
from jx_python.containers.list_usingPythonList import ListContainer
from mo_collections import not_right, not_left
from mo_dots import Data
from mo_files import File
from mo_future import text
from mo_logs import Log
from mo_math import mod, ceiling

FILENAME = "signatures"
DATA = File("../MySQL-to-S3")
MIN_POINTS = 6
MAX_POINTS = 24


def plot(data, title=None):
    fig = go.Figure(
        data=go.Scatter(x=tuple(range(0, len(data))), y=data, mode="markers")
    )
    fig.update_layout(title=title)
    fig.show()


# LOAD SOME RECENT RAPTOR MEASURES
def iterate_signatures():
    for file in DATA.children:
        if file.name.startswith(FILENAME + ".1705100"):
            Log.note("process {{file}}", file=file.abspath)
            process(file)

        # if file.name.startswith(FILENAME):
        #     Log.note("process {{file}}", file=file.abspath)
        #     process(file)


def process(file):
    sig = file.read_json()

    values = jx.run(
        {
            "from": ListContainer("sig", sig.performance_datum),
            "select": "value",
            "where": {"gte": {"push.time": {"date": "today-3month"}}},
            "sort": "push_time",
        }
    ).data

    segments = find_segments(values)
    assign_colors(
        values,
        segments,
        title="-".join(
            map(text, [sig.id, sig.suite, sig.test, sig.platform, sig.repository])
        ),
    )


scale = 5
operator_radius = 30
forward = np.exp(-np.arange(operator_radius) / scale) / scale
edge_operator = np.concatenate((-forward[::-1], forward))  # APPROX sign(x)*exp(abs(x))
TOP_EDGES = 0.05  # NUMBER OF POINTS TO INVESTIGATE EDGES (PERCENT)
COLORS = [
    "red",
    "green",
    "yellow",
    "blue",
    "purple",
    "pink",
    "orange",
    "cyan",
    "brown",
    "black",
]

P_THRESHOLD = pow(10, -4)
JITTER = 20  # NUMBER OF SAMPLES (+/-) TO LOOK FOR BETTER EDGES

def find_segments(values):
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
    plot(ranks, title="RANKS")
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
    plot(edge_detection, title="EDGES")
    top_edges = np.argsort(-np.abs(edge_detection))[:ceiling(len(values)*TOP_EDGES)]

    # SORT THE EDGE DETECTION
    segments = np.array([0, len(values)] + list(top_edges))
    segments = np.sort(segments)

    # CAN WE DO BETTER?
    for i, _ in enumerate(segments[:-2]):
        score, best_mid = jitter_MWU(
            logs, segments[i], segments[i + 1], segments[i + 2]
        )
        if score.pvalue < P_THRESHOLD:
            segments[i + 1] = best_mid
        else:
            # NO EVIDENCE OF DIFFERENCE, COLLAPSE SEGMENT
            segments[i + 1] = segments[i]

    segments = list(sorted(set(segments)))
    return segments


def assign_colors(values, segments, title):
    next_color = 0
    colors = ["gray"] * len(values)

    for i, _ in enumerate(segments[:-1]):
        start, end = segments[i], segments[i + 1]
        for i in range(start, end):
            colors[i] = COLORS[mod(next_color, len(COLORS))]
        next_color += 1

    fig = go.Figure(
        data=go.Scatter(
            x=tuple(range(0, len(values))),
            y=values,
            mode="markers",
            marker=dict(color=colors),
        )
    )
    fig.update_layout(title=title)
    fig.show()
    sleep(10)


def cumvar(values):
    m = np.arange(len(values))
    count = m + 1
    cummean = np.cumsum(values) / count
    cumvar  = ((values - cummean) ** 2) / m
    return cumvar


def cumSS(values):
    """
    RETURN CUMULATIVE SUM-OF-SQUARES
    :param values:
    """
    m = np.arange(len(values))
    count = m + 1
    cummean = np.cumsum(values) / count
    return ((values - cummean) ** 2)


def jitter_MWU(values, start, mid, end):
    # ADD SOME CONSTRAINTS TO THE RANGE OF VALUES TESTED
    m_start = min(mid, max(start + MIN_POINTS, mid - JITTER))
    m_end = max(mid, min(mid + JITTER, end - MIN_POINTS))
    if m_start == m_end:
        return Data(pvalue=1), mid
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

    # TOTAL SUM-OF-SQUARES
    v_prefix = not_right(not_left(cumSS(values[start:m_end]), m_start - start - 1), 1)
    v_suffix = not_right(cumSS(values[m_start:end][::-1])[::-1], end - m_end)
    v_score = v_prefix + v_suffix

    # PICK LOWEST
    pvalue = np.sqrt(m_score[:, 1] * v_score)  # GOEMEAN OF SCORES
    best = np.argmin(pvalue)

    return Data(pvalue=m_score[best, 1]), mids[best]


# MEASURE DEVIANCE (HOW TO KNOW THE START POINT?)
# SINCE LAST ALERT?
# SHOW MOST DEVIANT


iterate_signatures()
