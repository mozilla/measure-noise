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

import os

from perfalert import RevisionDatum, detect_changes

DEBUG = True
IS_TRAVIS = os.environ.get("TRAVIS")
SHOW_CHARTS = not IS_TRAVIS


def plot(data):
    if SHOW_CHARTS:
        import plotly.graph_objects as go

        fig = go.Figure(
            data=go.Scatter(x=tuple(range(0, len(data))), y=data, mode="markers")
        )
        fig.show()


def perfherder_alert(data):
    data = [RevisionDatum(i, i, [v]) for i, v in enumerate(data)]

    result = detect_changes(data)
    changes = [d for d in result if d.change_detected]
    return result, changes
