# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import division
from __future__ import unicode_literals

import numpy as np

import mo_math
from jx_bigquery import bigquery
from jx_bigquery.sql import sql_time, quote_column
from jx_mysql.mysql import MySQL
from jx_python import jx
from measure_noise import deviance
from measure_noise.extract_perf import get_signature, get_dataum
from measure_noise.step_detector import find_segments
from mo_dots import Null, Data, coalesce, unwrap, listwrap
from mo_future import text
from mo_json import NUMBER, python_type_to_json_type
from mo_logs import Log
from mo_sql import SQL
from mo_math.stats import median
from mo_threads import Till, Queue, Thread
from mo_times import Duration, Timer, Date, MONTH

NUM_THREADS = 5
IGNORE_TOP = 2  # IGNORE SOME OUTLIERS
LOOK_BACK = 3 * MONTH
MAX_RUNTIME = "50minute"  # STOP PROCESSING AFTER THIS GIVEN TIME

# REGISTER float64
python_type_to_json_type[np.float64] = NUMBER


def process(
    signature_hash,
    since,
    source,
    destination,
    show=False,
    show_limit=MAX_POINTS,
    show_old=True,
    show_distribution=None
):
    """
    :param signature_hash: The performance hash
    :param since: Only data after this date
    :param show:
    :param show_limit:
    :param show_old:
    :param show_distribution:
    :return:
    """
    if not mo_math.is_hex(signature_hash):
        Log.error("expecting hexidecimal hash")

    # GET SIGNATURE DETAILS
    sig = get_signature(source, signature_hash)

    # GET SIGNATURE DETAILS
    data = get_dataum(source, signature_hash, since)

    min_date = (Date.today() - 3 * MONTH).unix
    pushes = jx.sort(
        [
            {
                "value": median(rows.value),
                "runs": rows,
                "push": {"time": unwrap(t)["push.time"]},
            }
            for t, rows in jx.groupby(data, "push.time")
            if t["push\\.time"] > min_date
        ],
        "push.time",
    )

    values = list(pushes.value)
    title = "-".join(
        map(
            str,
            [
                sig.framework,
                sig.suite,
                sig.test,
                sig.platform,
                sig.repository,
            ],
        )
    )
    Log.note("With {{title}}", title=title)

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
            num_segments=len(new_segments)-1
        )

    destination.add(
        Data(
            id=signature_hash,
            title=title,
            num_pushes=len(values),
            num_segments=len(new_segments)-1,
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
    )


def main(config):
    outatime = Till(seconds=Duration(MAX_RUNTIME).total_seconds())
    outatime.then(lambda: Log.alert("Out of time, exit early"))
    since = Date.today()-LOOK_BACK

    # SETUP DESTINATION
    destination = bigquery.Dataset(config.destination).get_or_create_table(config.destination)
    # ENSURE SHARDS ARE MERGED
    destination.merge_shards()

    # GET ALL KNOWN SERIES
    with MySQL(config.source) as t:
        all_series = dict_to_data({
            doc['id']: doc
            for doc in t.query(SQL(f"""
                SELECT MAX(s.signature_hash) id
                FROM (            
                    SELECT d.signature_id, d.push_timestamp
                    FROM performance_datum d 
                    WHERE d.repository_id IN (77, 1)  -- autoland, mozilla-central
                    ORDER BY d.id desc
                    LIMIT 1000000
                ) d
                LEFT JOIN performance_signature s on s.id= d.signature_id
                WHERE s.test IS NULL or s.test='' or s.test=s.suite
                GROUP BY d.signature_id
                ORDER BY MAX(d.push_timestamp) DESC
            """))
        })

    # PULL PREVIOUS SERIES
    previous = dict_to_data({
        doc['id']: doc
        for doc in destination.query(SQL(f"""
            SELECT
                id,
                MAX(last_updated) as last_processed
            FROM
                {quote_column(destination.full_name)}
            WHERE
                last_updated > {sql_time(since)} AND
                num__pushes.__i__ > 0
            GROUP BY 
                id
            ORDER BY 
                MAX(last_updated)    
            LIMIT 
                5000
        """))
    })

    all_series = (all_series | previous).values()

    todo = jx.reverse(jx.sort(all_series, {"last_processed": "desc"})).limit(5000)
    needs_update = todo.get("id")
    Log.alert("{{num}} series are candidates for update", num=len(needs_update))

    limited_update = Queue("sigs")
    limited_update.extend(needs_update)

    with Timer("Updating local database"):
        def loop(please_stop):
            while not please_stop:
                sig_id = limited_update.pop_one()
                if not sig_id:
                    return
                try:
                    process(sig_id, since, config.source, destination)
                except Exception as cause:
                    Log.warning("Could not process {{sig}}", sig=sig_id, cause=cause)
        threads = [Thread.run(text(i), loop, please_stop=outatime) for i in range(NUM_THREADS)]
        for t in threads:
            t.join()

    destination.merge_shards()

    Log.note("Local database is up to date")


if __name__ == "__main__":
    with Log.start(app_name="etl") as config:
        main(config)


