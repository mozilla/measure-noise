import mo_math
import numpy as np

from jx_python import jx
from jx_sqlite.container import Container
from measure_noise import deviance
from measure_noise.extract_perf import get_worklist, get_signature, get_dataum
from measure_noise.step_detector import find_segments, MAX_POINTS
from measure_noise.utils import assign_colors
from mo_collections import left
from mo_dots import Null, wrap, Data, coalesce
from mo_files import File
from mo_future import text, first
from mo_logs import Log, startup, constants
from mo_math.stats import median
from mo_threads import Queue, Thread, THREAD_STOP
from mo_times import MONTH, Date, Timer, WEEK

FILENAME = "signatures"
DATA = File("../MySQL-to-S3")

config = Null


def process(sig_id, show=False, show_limit=MAX_POINTS):
    if not mo_math.is_integer(sig_id):
        Log.error("expecting integer id")
    sig = first(get_signature(config.database, sig_id))
    data = get_dataum(config.database, sig_id)

    min_date = (Date.today() - 3 * MONTH).unix
    pushes = wrap(
        [
            {"value": median(rows.value), "runs": rows, **t}
            for t, rows in jx.groupby(data, "push.time")
            if t["push\\.time"] > min_date
        ]
    )

    values = pushes.value

    title = "-".join(
        map(
            text,
            [
                sig.id,
                sig.framework,
                sig.suite,
                sig.test,
                sig.platform,
                sig.repository.name,
            ],
        )
    )
    Log.note("With {{title}}", title=title)

    with Timer("find segments"):
        new_segments, diffs = find_segments(
            values, sig.alert_change_type, sig.alert_threshold
        )

    old_alerts = [p for p in pushes if any(r.alert.id for r in p.runs)]
    old_segments = tuple(
        sorted(
            set(
                [0]
                + [
                    i
                    for i, p in enumerate(old_alerts)
                    if any(r.alert.id for r in p.runs)
                ]
                + [len(pushes)]
            )
        )
    )

    if len(new_segments) == 1:
        dev_status = None
        dev_score = None
        relative_noise = None
    else:
        # MEASURE DEVIANCE (HOW TO KNOW THE START POINT?)
        s, e = new_segments[-2], new_segments[-1]
        last_segment = np.array(values[s: e])
        dev_status, dev_score = deviance(last_segment)
        relative_noise = np.std(last_segment) / np.mean(last_segment)
        Log.note(
            "\n\tdeviance = {{deviance}}\n\tnoise={{std}}",
            title=title,
            deviance=(dev_status, dev_score),
            std=relative_noise,
        )

    # CHECK FOR OLD ALERTS
    max_diff = None
    is_diff = new_segments != old_segments
    if is_diff:
        # FOR MISSING POINTS, CALC BIGGEST DIFF
        max_diff = mo_math.MAX(
            d for s, d in zip(new_segments, diffs) if s not in old_segments
        )

        Log.alert("Disagree")
        Log.note("old={{old}}, new={{new}}", old=old_segments, new=new_segments)
        if show and len(pushes):
            assign_colors(values, old_segments, title="OLD " + title)
            assign_colors(values, new_segments, title="NEW " + title)
    else:
        Log.note("Agree")
        if show and len(pushes):
            assign_colors(values, old_segments, title="OLD " + title)
            assign_colors(values, new_segments, title="NEW " + title)

    summary_table.upsert(
        where={"eq": {"id": sig.id}},
        doc=Data(
            id=sig.id,
            title=title,
            num_pushes=len(pushes),
            is_diff=is_diff,
            max_diff=max_diff,
            num_new_segments=len(new_segments),
            num_old_segments=len(old_segments),
            relative_noise=relative_noise,
            dev_status=dev_status,
            dev_score=dev_score,
            last_updated=Date.now(),
        ),
    )


def is_diff(A, B):
    return A != B
    # if len(A) != len(B):
    #     return True
    #
    # for a, b in zip(A, B):
    #     if b - 5 <= a <= b + 5:
    #         continue
    #     else:
    #         return True
    # return False


RECENT = (Date.today() - WEEK).unix

if __name__ == "__main__":
    config = startup.read_settings(
        [
            {
                "name": "--now",
                "dest": "now",
                "help": "do not update signatures, go direct to showing problems with what is known locally",
                "action": "store_true",
            },
            {
                "name": ["--dev", "--deviant", "--deviance"],
                "dest": "deviant",
                "type": int,
                "help": "show number of top deviant series",
                "action": "store",
                "default": 0,
            },
            {
                "name": ["--noise", "--noisy"],
                "dest": "moise",
                "type": int,
                "help": "show number of top noisiest series",
                "action": "store",
                "default": 0,
            },
            {
                "name": ["--missing", "--missing-alerts"],
                "dest": "missing",
                "type": int,
                "help": "show number of missing alerts",
                "action": "store",
                "default": 0,
            },
        ]
    )
    constants.set(config.constants)
    try:
        Log.start(config.debug)

        local_container = Container(db=config.analysis.local_db)
        summary_table = local_container.get_or_create_facts("perf_summary")
        candidates = get_worklist(config.database)

        if not config.args.now:
            # GET EVERYTHING WE HAVE SO FAR
            exists = summary_table.query(
                {
                    "select": ["id", "last_updated"],
                    "where": {
                        "and": [
                            {"in": {"id": candidates.id}},
                            {"exists": "num_pushes"},
                        ]
                    },
                    "sort": "last_updated",
                    "limit": 100000,
                    "format": "list",
                }
            ).data
            # CHOOSE MISSING, THEN OLDEST, UP TO "RECENT"
            missing = list(set(candidates.id) - set(exists.id))

            needs_update = missing + [e for e in exists if e.last_updated < RECENT]
            Log.alert(
                "{{num}} series are candidates for local update",
                num=len(needs_update)
            )

            limited_update = Queue("sigs")
            limited_update.extend(left(needs_update, coalesce(config.analysis.limit, 100)))
            Log.alert("Updating {{num}} series", num=len(limited_update))

            def loop(please_stop):
                while not please_stop:
                    sig_id = limited_update.pop_one()
                    if not sig_id:
                        return
                    process(sig_id)

            threads = [Thread.run(text(i), loop) for i in range(3)]
            for t in threads:
                t.join()

            Log.note("Local database is up to date")

        if config.args.deviant:
            tops = summary_table.query(
                {
                    "select": "id",
                    "where": {
                        "and": [
                            {"in": {"id": candidates.id}},
                            {"gte": {"num_pushes": 1}},
                        ]
                    },
                    "sort": {"value": {"abs": "dev_score"}, "sort": "desc"},
                    "limit": config.args.deviant,
                    "format": "list",
                }
            ).data

            for id in tops:
                process(id, show=True)

    except Exception as e:
        Log.warning("Problem with perf scan", e)
    finally:
        Log.stop()
