import plotly.graph_objects as go

from perfalert import RevisionDatum, detect_changes

DEBUG = True
SHOW_CHARTS = False


def plot(data):
    if SHOW_CHARTS:
        fig = go.Figure(data=go.Scatter(
            x=tuple(range(0, len(data))),
            y=data,
            mode='markers'
        ))
        fig.show()


def perfherder_alert(data):
    data = [
        RevisionDatum(i, i, [v])
        for i, v in enumerate(data)
    ]

    result = detect_changes(data)
    changes = [d for d in result if d.change_detected]
    return result, changes
