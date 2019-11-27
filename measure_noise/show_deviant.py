import numpy as np

from jx_python import jx
from jx_sqlite.container import Container
from measure_noise import deviance
from measure_noise.extract_perf import get_worklist, get_signature, get_dataum
from measure_noise.step_detector import find_segments, MAX_POINTS
from measure_noise.utils import assign_colors
from mo_dots import Null, wrap, Data
from mo_files import File
from mo_future import text, first
from mo_logs import Log, startup, constants
from mo_math.stats import median
from mo_times import MONTH, Date, Timer, WEEK

FILENAME = "signatures"
DATA = File("../MySQL-to-S3")

config = Null


def process(sig_id):
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
        new_segments = find_segments(values, sig.alert_change_type, sig.alert_threshold)

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

    # MEASURE DEVIANCE (HOW TO KNOW THE START POINT?)
    s, e = new_segments[-2], new_segments[-1]
    last_segment = np.array(values[max(s, e - MAX_POINTS) : e])
    dev_status, dev_score = deviance(last_segment)
    relative_noise = np.std(last_segment) / np.mean(last_segment)
    Log.note(
        "\n\tdeviance = {{deviance}}\n\tnoise={{std}}",
        title=title,
        deviance=(dev_status, dev_score),
        std=relative_noise,
    )

    # CHECK FOR OLD ALERTS
    is_diff = new_segments != old_segments
    if is_diff:
        Log.alert("Disagree")
        Log.note("old={{old}}, new={{new}}", old=old_segments, new=new_segments)
        if len(candidates) < 10:
            assign_colors(values, old_segments, title="OLD " + title)
            assign_colors(values, new_segments, title="NEW " + title)
    else:
        Log.note("Agree")
        if len(candidates) < 10:
            assign_colors(values, old_segments, title="OLD " + title)
            assign_colors(values, new_segments, title="NEW " + title)

    summary_table.upsert(
        where={"eq": {"id": sig.id}},
        doc=Data(
            id=sig.id,
            title=title,
            is_diff=is_diff,
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
                "help": "do not update signatures, go direct to showing problems with what is known locally",
                "action": "store_true",
            },
            {
                "name": "--num",
                "help": "number of top differences to show in browser",
                "action": "store",
                "default": 10,
            },
        ]
    )
    constants.set(config.constants)
    try:
        Log.start(config.debug)

        local_container = Container(db=config.local_db)
        summary_table = local_container.get_or_create_facts("perf_summary")
        candidates = get_worklist(config.database)

        if not config.args.now:
            # GET EVERYTHING WE HAVE SO FAR
            exists = summary_table.query(
                {
                    "select": ["id", "last_updated"],
                    "where": {"in": {"id": candidates.id}},
                    "sort": "last_updated",
                    "format": "list"
                }
            ).data
            # CHOOSE MISSING, THEN OLDEST, UP TO "RECENT"
            missing = list(set(candidates.id) - set(exists.id))

            todo = missing + [e for e in exists if e.last_updated < RECENT]
            Log.alert("Processing {{num}} series", num=len(todo))
            for sig_id in todo:
                process(sig_id)

            Log.note("Local database is up to date")

        tops = summary_table.query(
            {
                "select": "id",
                "where": {"in": {"id": candidates.id}},
                "sort": {"value": {"abs": "dev_score"}, "sort": "desc"},
                "limit": config.args.num,
                "format": "list"
            }
        ).data

        for id in tops:
            process(id)

    except Exception as e:
        Log.warning("Problem with perf scan", e)
    finally:
        Log.stop()
