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

import webbrowser

import numpy as np

import mo_math
from jx_base import jx_expression
from jx_base.expressions import TRUE
from jx_bigquery import bigquery
from jx_bigquery.expressions import BQLang
from jx_bigquery.sql import quote_column, quote_value, sql_iso
from jx_python import jx
from moz_measure_noise import deviance, step_detector
from moz_measure_noise.extract_perf import get_signature, get_dataum
from moz_measure_noise.step_detector import find_segments, MAX_POINTS, MIN_POINTS
from moz_measure_noise.utils import assign_colors, histogram
from mo_collections import left
from mo_dots import Data, coalesce, unwrap, to_data, listwrap
from mo_files import File
from mo_files.url import value2url_param
from mo_future import text
from mo_logs import Log, startup, constants
from mo_math.stats import median
from mo_threads import Queue, Thread
from mo_times import Date, Timer, Duration
from mo_times.dates import parse
from pyLibrary.convert import list2tab

IGNORE_TOP = 3  # WHEN CALCULATING NOISE OR DEVIANCE, IGNORE SOME EXTREME VALUES
LOCAL_RETENTION = "3day"  # HOW LONG BEFORE WE REFRESH LOCAL DATABASE ENTRIES
# WHEN COMPARING new AND old STEPS, THE NUMBER OF PUSHES TO CONSIDER THEM STILL EQUAL
TOLERANCE = MIN_POINTS
SCATTER_RANGE = "6month"  # TIME RANGE TO SHOW IN SCATTER PLOT
TREEHERDER_RANGE = "365day"  # TIME RANGE TO SHOW ON PERFHERDER
DOWNLOAD_LIMIT = 100_000


def process(
    about_deviant,
    since,
    source,
    deviant_summary,
    show=False,
    show_limit=MAX_POINTS,
    show_old=False,
    show_distribution=None,
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
    sig_id = about_deviant.id
    if not isinstance(sig_id, int):
        Log.error("expecting id")

    # GET SIGNATURE DETAILS
    sig = get_signature(db_config=source, signature_id=sig_id)

    # GET SIGNATURE DETAILS
    data = get_dataum(source, sig.id, since=since, limit=show_limit)

    min_date = since.unix
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
                sig.id,
                sig.framework,
                sig.suite,
                sig.test,
                sig.repository,
                sig.platform,
                about_deviant.overall_dev_status,
            ],
        )
    )
    # EG https://treeherder.mozilla.org/perf.html#/graphs?highlightAlerts=1&series=mozilla-central,fee739b45f7960e4a520d8e0bd781dd9d0a3bec4,1,10&timerange=31536000
    url = "https://treeherder.mozilla.org/perf.html#/graphs?" + value2url_param({
        "highlightAlerts": 1,
        "series": [sig.repository, sig.id, 1, coalesce(sig.framework_id, sig.framework)],
        "timerange": Duration(TREEHERDER_RANGE).seconds
    })

    Log.note("With {{title}}: {{url}}", title=title, url=url)

    with Timer("find segments"):
        new_segments, new_diffs = find_segments(
            values, sig.alert_change_type, sig.alert_threshold
        )

    # USE PERFHERDER ALERTS TO IDENTIFY OLD SEGMENTS
    old_segments = tuple(
        sorted(
            set(
                [i for i, p in enumerate(pushes) if any(r.alert.id for r in p.runs)]
                + [0, len(pushes)]
            )
        )
    )
    old_medians = [0.0] + [
        np.median(values[s:e]) for s, e in zip(old_segments[:-1], old_segments[1:])
    ]
    old_diffs = np.array(
        [b / a - 1 for a, b in zip(old_medians[:-1], old_medians[1:])] + [0]
    )

    if len(new_segments) == 1:
        overall_dev_status = None
        overall_dev_score = None
        last_mean = None
        last_std = None
        last_dev_status = None
        last_dev_score = None
        relative_noise = None
        Log.note("not ")
    else:
        # NOISE OF LAST SEGMENT
        s, e = new_segments[-2], new_segments[-1]
        last_segment = np.array(values[s:e])
        ignore = IGNORE_TOP
        trimmed_segment = last_segment[np.argsort(last_segment)[ignore:-ignore]]
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

        if show_distribution:
            histogram(
                trimmed_segment, title=last_dev_status + "=" + text(last_dev_score)
            )

    max_extra_diff = None
    max_missing_diff = None
    _is_diff = is_diff(new_segments, old_segments)
    if _is_diff:
        # FOR MISSING POINTS, CALC BIGGEST DIFF
        max_extra_diff = mo_math.MAX(
            abs(d)
            for s, d in zip(new_segments, new_diffs)
            if all(not (s - TOLERANCE <= o <= s + TOLERANCE) for o in old_segments)
        )
        max_missing_diff = mo_math.MAX(
            abs(d)
            for s, d in zip(old_segments, old_diffs)
            if all(not (s - TOLERANCE <= n <= s + TOLERANCE) for n in new_segments)
        )

        Log.alert(
            "Disagree max_extra_diff={{max_extra_diff|round(places=3)}}, max_missing_diff={{max_missing_diff|round(places=3)}}",
            max_extra_diff=max_extra_diff,
            max_missing_diff=max_missing_diff,
        )
        Log.note("old={{old}}, new={{new}}", old=old_segments, new=new_segments)
    else:
        Log.note("Agree")

    if show and len(pushes):
        show_old and assign_colors(values, old_segments, title="OLD " + title)
        assign_colors(values, new_segments, title="NEW " + title)
        if url:
            webbrowser.open(url)

    if isinstance(deviant_summary, bigquery.Table):
        Log.note("BigQuery summary not updated")
        return

    deviant_summary.upsert(
        where={"eq": {"id": sig.id}},
        doc=Data(
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
            is_diff=_is_diff,
            max_extra_diff=max_extra_diff,
            max_missing_diff=max_missing_diff,
            num_new_segments=len(new_segments),
            num_old_segments=len(old_segments),
        ),
    )


def is_diff(A, B):
    if len(A) != len(B):
        return True

    for a, b in zip(A, B):
        if b - TOLERANCE <= a <= b + TOLERANCE:
            continue
        else:
            return True
    return False


def update_local_database(config, deviant_summary, candidates, since):
    if isinstance(deviant_summary, bigquery.Table):
        Log.note("Only the ETL process should fill the bigquery table")
        return

    # GET EVERYTHING WE HAVE SO FAR
    exists = deviant_summary.query(
        {
            "select": ["signature_hash", "last_updated"],
            "where": {
                "and": [
                    {"in": {"signature_hash": candidates.signature_hash}},
                    {"exists": "num_pushes"},
                ]
            },
            "sort": "last_updated",
            "limit": 100000,
            "format": "list",
        }
    ).data
    # CHOOSE MISSING, THEN OLDEST, UP TO "RECENT"
    missing = list(set(candidates.signature_hash) - set(exists.signature_hash))

    too_old = Date.today() - parse(LOCAL_RETENTION)
    needs_update = missing + [
        e.signature_hash for e in exists if e.last_updated < too_old.unix
    ]
    Log.alert("{{num}} series are candidates for local update", num=len(needs_update))

    limited_update = Queue("sigs")
    limited_update.extend(
        left(needs_update, coalesce(config.display.download_limit, 100))
    )
    Log.alert("Updating local database with {{num}} series", num=len(limited_update))

    with Timer("Updating local database"):

        def loop(please_stop):
            while not please_stop:
                signature_hash = limited_update.pop_one()
                if not signature_hash:
                    return
                process(
                    signature_hash,
                    since,
                    source=config.database,
                    deviant_summary=deviant_summary,
                )

        threads = [Thread.run(text(i), loop) for i in range(3)]
        for t in threads:
            t.join()

    Log.note("Local database is up to date")


def show_sorted(
    config,
    since,
    source,
    deviant_summary,
    sort,
    limit,
    where=TRUE,
    show_distribution=None,
    show_old=False,
):
    if not limit:
        return

    tops = list(
        deviant_summary.jx_query(
            {
                "where": {"and": [where, config.analysis.interesting]},
                "sort": sort,
                "limit": limit,
                "format": "list",
            }
        ).data
    )

    for doc in tops:
        process(
            about_deviant=to_data(doc),
            since=since,
            source=source,
            deviant_summary=deviant_summary,
            show=True,
            show_distribution=show_distribution,
            show_old=show_old,
        )


def enrich_download_docs(docs):
    template_url = (
        'https://treeherder.mozilla.org/perf.html#/graphs'
        '?series={0[repository]},{0[id]},1,{0[framework_id]}'
        '&timerange=31536000'
    )

    def enrich(doc):
        doc['perfherder_link'] = template_url.format(doc)
        return doc

    return [enrich(doc) for doc in docs]


def main():
    since = Date.today() - Duration(SCATTER_RANGE)

    if config.database.host not in listwrap(config.analysis.expected_database_host):
        Log.error("Expecting database to be one of {{expected}}", expected=config.analysis.expected_database_host)
    if not config.analysis.interesting:
        Log.alert("Expecting config file to have `analysis.interesting` with a json expression.  All series are included.")

    # SETUP DESTINATION
    deviant_summary = bigquery.Dataset(config.deviant_summary).get_or_create_table(
        read_only=True, kwargs=config.deviant_summary
    )

    if config.args.id:
        # EXIT EARLY AFTER WE GOT THE SPECIFIC IDS
        if len(config.args.id) < 4:
            step_detector.SHOW_CHARTS = True
        for signature_hash in config.args.id:
            process(
                signature_hash,
                since=since,
                source=config.database,
                deviant_summary=deviant_summary,
                show=True,
            )
        return

    # DOWNLOAD
    if config.args.download:
        # GET INTERESTING SERIES
        where_clause = BQLang[jx_expression(config.analysis.interesting)].to_bq(
            deviant_summary.schema
        )

        # GET ALL KNOWN SERIES
        docs = list(
            deviant_summary.sql_query(f"""
                SELECT * EXCEPT (_rank, values) 
                FROM (
                  SELECT 
                    *, 
                    row_number() over (partition by id order by last_updated desc) as _rank 
                  FROM  
                    {quote_column(deviant_summary.full_name)}
                  ) a 
                WHERE _rank=1 and {sql_iso(where_clause)}
                LIMIT {quote_value(DOWNLOAD_LIMIT)}
            """
            )
        )
        Log.note("Downloaded {{num}} series", num=len(docs))
        if len(docs) == DOWNLOAD_LIMIT:
            Log.warning("Not all signatures downloaded")
        docs = enrich_download_docs(docs)
        File(config.args.download).write(list2tab(docs, separator=","))

    # DEVIANT
    show_sorted(
        config=config,
        since=since,
        source=config.database,
        deviant_summary=deviant_summary,
        sort={"value": {"abs": "overall_dev_score"}, "sort": "desc"},
        limit=config.args.deviant,
        show_old=False,
        show_distribution=True,
    )

    # MODAL
    show_sorted(
        config=config,
        since=since,
        source=config.database,
        deviant_summary=deviant_summary,
        sort="overall_dev_score",
        limit=config.args.modal,
        where={"eq": {"overall_dev_status": "MODAL"}},
        show_distribution=True,
    )

    # OUTLIERS
    show_sorted(
        config=config,
        since=since,
        source=config.database,
        deviant_summary=deviant_summary,
        sort={"value": "overall_dev_score", "sort": "desc"},
        limit=config.args.outliers,
        where={"eq": {"overall_dev_status": "OUTLIERS"}},
        show_distribution=True,
    )

    # SKEWED
    show_sorted(
        config=config,
        since=since,
        source=config.database,
        deviant_summary=deviant_summary,
        sort={"value": {"abs": "overall_dev_score"}, "sort": "desc"},
        limit=config.args.skewed,
        where={"eq": {"overall_dev_status": "SKEWED"}},
        show_distribution=True,
    )

    # OK
    show_sorted(
        config=config,
        since=since,
        source=config.database,
        deviant_summary=deviant_summary,
        sort={"value": {"abs": "overall_dev_score"}, "sort": "desc"},
        limit=config.args.ok,
        where={"eq": {"overall_dev_status": "OK"}},
        show_distribution=True,
    )

    # NOISE
    show_sorted(
        config=config,
        since=since,
        source=config.database,
        deviant_summary=deviant_summary,
        sort={"value": {"abs": "relative_noise"}, "sort": "desc"},
        where={"gte": {"num_pushes": 30}},
        limit=config.args.noise,
    )

    # EXTRA
    show_sorted(
        config=config,
        since=since,
        source=config.database,
        deviant_summary=deviant_summary,
        sort={"value": {"abs": "max_extra_diff"}, "sort": "desc"},
        where={"lte": {"num_new_segments": 7}},
        limit=config.args.extra,
    )

    # MISSING
    show_sorted(
        config=config,
        since=since,
        source=config.database,
        deviant_summary=deviant_summary,
        sort={"value": {"abs": "max_missing_diff"}, "sort": "desc"},
        where={"lte": {"num_old_segments": 6}},
        limit=config.args.missing,
    )

    # PATHOLOGICAL
    show_sorted(
        config=config,
        since=since,
        source=config.database,
        deviant_summary=deviant_summary,
        sort={"value": "num_segments", "sort": "desc"},
        limit=config.args.pathological,
    )


if __name__ == "__main__":
    config = startup.read_settings(
        [
            {
                "name": ["--id", "--key", "--ids", "--keys"],
                "dest": "id",
                "nargs": "*",
                "type": int,
                "help": "show specific signatures",
            },
            {
                "name": "--download",
                "dest": "download",
                "help": "download deviance to CSV local file",
                "nargs": "?",
                "const": "deviant_stats.csv",
                "type": str,
                "action": "store",
            },
            {
                "name": ["--dev", "--deviant", "--deviance"],
                "dest": "deviant",
                "nargs": "?",
                "const": 10,
                "type": int,
                "help": "show number of top deviant series",
                "action": "store",
            },
            {
                "name": ["--modal"],
                "dest": "modal",
                "nargs": "?",
                "const": 10,
                "type": int,
                "help": "show number of top modal series",
                "action": "store",
            },
            {
                "name": ["--outliers"],
                "dest": "outliers",
                "nargs": "?",
                "const": 10,
                "type": int,
                "help": "show number of top outliers series",
                "action": "store",
            },
            {
                "name": ["--skewed", "--skew"],
                "dest": "skewed",
                "nargs": "?",
                "const": 10,
                "type": int,
                "help": "show number of top skewed series",
                "action": "store",
            },
            {
                "name": ["--ok"],
                "dest": "ok",
                "nargs": "?",
                "const": 10,
                "type": int,
                "help": "show number of top worst OK series",
                "action": "store",
            },
            {
                "name": ["--noise", "--noisy"],
                "dest": "noise",
                "nargs": "?",
                "const": 10,
                "type": int,
                "help": "show number of top noisiest series",
                "action": "store",
            },
            {
                "name": ["--extra", "-e"],
                "dest": "extra",
                "nargs": "?",
                "const": 10,
                "type": int,
                "help": "show number of series that are missing perfherder alerts",
                "action": "store",
            },
            {
                "name": ["--missing", "--miss", "-m"],
                "dest": "missing",
                "nargs": "?",
                "const": 10,
                "type": int,
                "help": "show number of series which are missing alerts over perfherder",
                "action": "store",
            },
            {
                "name": ["--pathological", "--pathological", "--pathology", "-p"],
                "dest": "pathological",
                "nargs": "?",
                "const": 3,
                "type": int,
                "help": "show number of series that have most edges",
                "action": "store",
            },
        ]
    )
    constants.set(config.constants)
    try:
        Log.start(config.debug)
        main()
    except Exception as e:
        Log.warning("Problem with perf scan", e)
    finally:
        Log.stop()
