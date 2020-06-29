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

import plotly.graph_objects as go

from mo_math import mod


def histogram(values, title=None):
    fig = go.Figure(
        go.Histogram(x=list(values))
    )
    fig.update_layout(title=title)
    fig.show()


def plot(data, title=None):
    fig = go.Figure(
        data=go.Scatter(x=tuple(range(0, len(data))), y=data, mode="markers")
    )
    fig.update_layout(title=title)
    fig.show()


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
