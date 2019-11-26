import time

from jx_python import jx
from measure_noise.extract_perf import get_worklist, get_signature, get_dataum
from measure_noise.step_detector import find_segments
from measure_noise.utils import assign_colors
from mo_dots import Null, wrap
from mo_files import File
from mo_future import text, first
from mo_logs import Log, startup, constants
from mo_math.stats import median
from mo_times import MONTH, Date

FILENAME = "signatures"
DATA = File("../MySQL-to-S3")

config = Null


def process(sig_id):
    sig = first(get_signature(config.database, sig_id))
    data = get_dataum(config.database, sig_id)

    min_date = (Date.today() - 3 * MONTH).unix
    pushes = wrap([
        {"value": median(rows.value), "runs": rows, **t}
        for t, rows in jx.groupby(data, "push.time")
        if t["push\\.time"] > min_date
    ])

    values = pushes.value
    segments = find_segments(values, sig.alert_change_type, sig.alert_threshold)

    # CHECK FOR OLD ALERTS
    if len(segments)>1:
        pass
        time.sleep(10)

    assign_colors(
        values,
        segments,
        title="-".join(
            map(text, [sig.id, sig.suite, sig.test, sig.platform, sig.repository])
        ),
    )




# MEASURE DEVIANCE (HOW TO KNOW THE START POINT?)
# SINCE LAST ALERT?
# SHOW MOST DEVIANT


if __name__ == "__main__":
    config = startup.read_settings()
    constants.set(config.constants)
    try:
        Log.start(config.debug)
        for sig in get_worklist(config.database):
            process(sig.id)
    except Exception as e:
        Log.warning("Problem with perf scan", e)
    finally:
        Log.stop()
