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

from mo_dots import Null
from mo_math import mod

go = Null


def _late_import():
    global go
    import plotly.graph_objects as go

    _ = go


def get_range(value):
    """
    RETURN THE RANGE THAT SHOWS MOST POINTS
    """
    all_values = np.array(value)
    num_raw_samples = len(value)
    ignore = int(num_raw_samples / 20)
    if not ignore:
        trimmed_segment = all_values
    else:
        trimmed_segment = all_values[np.argsort(all_values)[ignore:-ignore]]
    t_min, t_max = np.min(trimmed_segment), np.max(trimmed_segment)
    # a_max = np.max(all_values)

    if t_max == t_min:
        t_max = t_min + 1

    padding = max(t_max / 10, (t_max - t_min) / 10)
    t_min = t_min - padding
    t_max = t_max + padding

    return t_min, t_max


def histogram(values, title=None):
    _late_import()
    fig = go.Figure(go.Histogram(x=list(values)))
    fig.update_layout(title=title)
    fig.show()


def plot(data, title=None):
    _late_import()

    fig = go.Figure(
        data=go.Scatter(
            x=tuple(range(0, len(data))),
            y=data,
            mode="markers",
            yaxis=dict(range=get_range(data), constrain="domain"),
        )
    )
    fig.update_layout(title=title)
    fig.show()


def assign_colors(values, segments, title):
    _late_import()
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
    fig.update_layout(yaxis=dict(range=get_range(values), constrain="range"))
    fig.show()


COLORS = [
    "red",
    "green",
    "blue",
    "purple",
    "pink",
    "orange",
    "cyan",
    "brown",
    "black",
    "yellow",
]
