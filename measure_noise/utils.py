from time import sleep

import plotly.graph_objects as go

from mo_math import mod


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
    sleep(10)


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
