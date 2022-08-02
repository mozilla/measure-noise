# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Perftest Team (perftest@mozilla.com)
#
from __future__ import division
from __future__ import unicode_literals

import numpy as np

from jx_python import jx
from moz_measure_noise import deviance
from moz_measure_noise.extract_perf import get_signature, get_dataum
from moz_measure_noise.step_detector import find_segments
from mo_dots import Data, unwrap
from mo_json import NUMBER, python_type_to_json_type, scrub
from mo_logs import Log
from mo_math.stats import median
from mo_times import Timer, Date

LIMIT = 5000

# REGISTER float64
python_type_to_json_type[np.float64] = NUMBER


def process(
    sig_id, since, source, destination,
):
    """
    :param sig_id: The performance hash
    :param since: Only data after this date
    :param show:
    :param show_limit:
    :param show_old:
    :param show_distribution:
    :return:
    """
    if not isinstance(sig_id, int):
        Log.error("expecting id")

    # GET SIGNATURE DETAILS
    sig = get_signature(source, sig_id)

    # GET SIGNATURE DETAILS
    pushes = get_dataum(source, sig_id, since, LIMIT)

    pushes = jx.sort(
        [
            {
                "value": median(rows.value),
                "runs": rows,
                "push": {"time": unwrap(t)["push.time"]},
            }
            for t, rows in jx.groupby(pushes, "push.time")
            if t["push\\.time"] > since
        ],
        "push.time",
    )

    values = list(pushes.value)
    title = "-".join(
        map(str, [sig.framework, sig.suite, sig.test, sig.platform, sig.repository,],)
    )
    Log.note("With {{title}}", title=title)

    if len(values) > LIMIT:
        Log.alert(
            "Too many values for {{title}} ({at least {num}}), choosing last {{limit}}",
            title=title,
            num=len(values),
            limit=LIMIT,
        )
        values = values[-LIMIT:]

    with Timer("find segments"):
        new_segments, new_diffs = find_segments(
            values, sig.alert_change_type, sig.alert_threshold
        )

    if len(new_segments) == 1:
        overall_dev_status = None
        overall_dev_score = None
        last_mean = None
        last_std = None
        last_dev_status = None
        last_dev_score = None
        relative_noise = None
    else:
        # NOISE OF LAST SEGMENT
        s, e = new_segments[-2], new_segments[-1]
        last_segment = np.array(values[s:e])
        trimmed_segment = last_segment
        last_mean = np.mean(trimmed_segment)
        last_std = np.std(trimmed_segment)
        last_dev_status, last_dev_score = deviance(trimmed_segment)
        relative_noise = last_std / last_mean

        # FOR EACH SEGMENT, NORMALIZE MEAN AND VARIANCE
        normalized = []
        for s, e in jx.pairs(new_segments):
            data = np.array(values[s:e])
            norm = (data + last_mean - np.mean(data)) * last_std / np.std(data)
            normalized.extend(norm)

        overall_dev_status, overall_dev_score = deviance(normalized)
        Log.note(
            "\n\tdeviance = {{deviance}}\n\tnoise={{std}}\n\tpushes={{pushes}}\n\tsegments={{num_segments}}",
            title=title,
            deviance=(overall_dev_status, overall_dev_score),
            std=relative_noise,
            pushes=len(values),
            num_segments=len(new_segments) - 1,
        )

    destination.add(
        Data(
            id=sig_id,
            title=title,
            num_pushes=len(values),
            num_segments=len(new_segments) - 1,
            relative_noise=relative_noise,
            overall_dev_status=overall_dev_status,
            overall_dev_score=overall_dev_score,
            last_mean=last_mean,
            last_std=last_std,
            last_dev_status=last_dev_status,
            last_dev_score=last_dev_score,
            last_updated=Date.now(),
            values=values,
        )
        | scrub(sig)
    )
