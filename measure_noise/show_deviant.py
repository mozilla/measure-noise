import numpy as np
import plotly.graph_objects as go
from scipy.stats import stats, rankdata
from time import sleep

from jx_python import jx
from jx_python.containers.list_usingPythonList import ListContainer
from mo_dots import Data
from mo_files import File
from mo_future import text
from mo_logs import Log
from mo_math import mod

FILENAME = "signature"
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
        if file.name.startswith(FILENAME):
            Log.note("process {{file}}", file=file.abspath)
            process(file)


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
    # values = unwrap(jx.sort(sig.performance_datum, "push.time").value)
    # coord = (0, 238, 287)
    # s, m, e = coord

    def color(i):
        if 0 <= i < s:
            return "black"
        if s <= i < m:
            return "red"
        if m <= i < e:
            return "green"
        return "black"

    # fig = go.Figure(
    #     data=go.Scatter(
    #         x=tuple(range(0, len(values))),
    #         y=values,
    #         mode="markers",
    #         marker=dict(color=[color(i) for i, v in enumerate(values)]),
    #     )
    # )
    # fig.show()

    find_edges(values, title="-".join(map(text, [sig.id, sig.suite, sig.test, sig.platform, sig.repository])))

    # it = all_combos(values)
    # best_coord, best_p = it.__next__()
    #
    # for coord, p in it:
    #     if best_p.pvalue > p.pvalue:
    #         best_coord = coord
    #         best_p = p
    #
    # s, m, e = best_coord
    #
    # Log.note("coord={{coord}}, p={{p}}", coord=best_coord, p=best_p.pvalue)
    # fig = go.Figure(
    #     data=go.Scatter(
    #         x=tuple(range(0, len(values))),
    #         y=values,
    #         mode="markers",
    #         marker=dict(color=[color(i) for i, v in enumerate(values)]),
    #     )
    # )
    # fig.show()


scale = 5
filter_radius = 30
forward = np.exp(-np.arange(filter_radius) / scale) / scale
edge_filter = np.concatenate((-forward[::-1], forward))  # APPROX sign(x)*exp(abs(x))
# plot(edge_filter, title="filter")
COLORS = ["red", "green", "yellow", "blue", "purple", "pink", "orange", "cyan", "brown", "black"]

P_THRESHOLD = pow(10, -3)


def find_edges(values, title=None):
    values = np.array(values)

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
    extra = (
        np.concatenate(
            (
                np.repeat(ranks[0], filter_radius),
                ranks,
                np.repeat(ranks[-1], filter_radius),
            )
        )
        - 1
    ) / len(values)
    edge_detection = np.convolve(extra, edge_filter, mode="valid")
    plot(edge_detection)
    top_edges = np.argsort(-np.abs(edge_detection))[:20]


    # SORT THE EDGE DETECTION
    segments = np.array(
        [0, len(values)]+list(top_edges)
    )
    segments = np.sort(segments)

    # CAN WE DO BETTER?
    for i, _ in enumerate(segments[:-2]):
        score, best_mid = vary(ranks, segments[i], segments[i+1], segments[i+2])
        if score.pvalue < P_THRESHOLD:
            segments[i + 1] = best_mid
        else:
            segments[i + 1] = segments[i]

    segments = list(sorted(set(segments)))

    next_color = [0]
    colors = ["gray"] * len(values)
    pvalues = [1]*len(values)

    def assign_color(start, end, pvalue):
        for i in range(start, end):
            if pvalues[i] > pvalue:
                pvalues[i] = pvalue
                colors[i] = COLORS[mod(next_color[0], len(COLORS))]
        next_color[0] = next_color[0] + 1

    for i, _ in enumerate(segments[:-1]):
        assign_color(segments[i], segments[i+1], 0)


    # # CALCULATE SLOPES
    # maxi, mini = np.meshgrid(best_edges[:10], best_edges[-10:])
    # temp = zip(*np.ndenumerate(-abs((edge_detection[maxi] - edge_detection[mini]) / (maxi - mini))))
    # slope_coord, slopes = temp
    # best_slopes = np.argsort(slopes)
    #
    # for num_tried, segment in enumerate(best_slopes):
    #     # FOR GIVEN SEGMENT FIND BEST EVIDENCE OF DIFFERENCE
    #     try_more = False
    #     coord = slope_coord[segment]
    #     start, end = sorted([maxi[coord], mini[coord]])
    #
    #     x = values[start:end]
    #     post_score, post_index = best_MWU(x, values[end:])
    #     if post_score.pvalue < P_THRESHOLD:
    #         assign_color(start, end, post_score.pvalue)
    #         try_more = True
    #         assign_color(end, end+post_index, post_score.pvalue)
    #
    #     pre_score, pre_index = best_MWU(x, values[:start][::-1])
    #     if pre_score.pvalue < P_THRESHOLD:
    #         if not try_more:
    #             assign_color(start, end, pre_score.pvalue)
    #         try_more = True
    #         assign_color(start - pre_index, start, pre_score.pvalue)
    #
    #     if not try_more and num_tried > 20:
    #         break

    if next_color[0]:
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


def best_MWU(reference, residue):
    best_score = Data(pvalue=1)
    best_end = -1
    for e in range(MIN_POINTS, len(residue)):
        r = residue[0:e]
        score = stats.mannwhitneyu(
            reference, r, use_continuity=True, alternative="two-sided"
        )
        if best_score.pvalue > score.pvalue:
            best_score = score
            best_end = e
    return best_score, best_end


def vary(values, start, mid, end):
    best_score = Data(pvalue=1)
    best_mid = -1
    for m in range(min(mid, max(start+MIN_POINTS, mid-20)), max(mid, min(mid+20, end-MIN_POINTS))):
        score = stats.mannwhitneyu(
            values[start:m], values[m:end], use_continuity=True, alternative="two-sided"
        )
        if best_score.pvalue > score.pvalue:
            best_score = score
            best_mid = m
    return best_score, best_mid





def all_combos(values):
    values = np.array(values)
    num = len(values)
    for s in range(num - MIN_POINTS - MIN_POINTS):
        for m in range(s + MIN_POINTS, min(s + MAX_POINTS, num)):
            for e in range(m + MIN_POINTS, min(m + MAX_POINTS, num)):
                # USE MANN-WHITNEY TO FIND DISJOINT BITS, AND AMPLITUDE
                x = values[s:m]
                y = values[m:e]
                p = stats.mannwhitneyu(
                    x, y, use_continuity=True, alternative="two-sided"
                )
                yield (s, m, e), p


# MEASURE DEVIANCE (HOW TO KNOW THE START POINT?)
# SINCE LAST ALERT?


# SHOW MOST DEVIANT


iterate_signatures()
