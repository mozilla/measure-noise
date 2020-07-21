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

from mo_future import is_text, is_binary
import sys
from time import time

from mo_dots import Data
from mo_future import PY3, text
from mo_logs import Log
from mo_logs.log_usingNothing import StructuredLogger
from mo_logs.strings import CR, expand_template
from mo_threads import THREAD_STOP, Thread, Till

DEBUG_LOGGING = False


class StructuredLogger_usingThreadedStream(StructuredLogger):
    # stream CAN BE AN OBJCET WITH write() METHOD, OR A STRING
    # WHICH WILL eval() TO ONE
    def __init__(self, stream):
        assert stream

        if is_text(stream):
            name = stream
            stream = self.stream = eval(stream)
            if name.startswith("sys.") and PY3:
                self.stream = Data(write=lambda d: stream.write(d.decode('utf8')))
        else:
            name = "stream"
            self.stream = stream

        # WRITE TO STREAMS CAN BE *REALLY* SLOW, WE WILL USE A THREAD
        from mo_threads import Queue

        def utf8_appender(value):
            if is_text(value):
                value = value.encode('utf8')
            self.stream.write(value)

        appender = utf8_appender

        self.queue = Queue("queue for " + self.__class__.__name__ + "(" + name + ")", max=10000, silent=True)
        self.thread = Thread("log to " + self.__class__.__name__ + "(" + name + ")", time_delta_pusher, appender=appender, queue=self.queue, interval=0.3)
        self.thread.parent.remove_child(self.thread)  # LOGGING WILL BE RESPONSIBLE FOR THREAD stop()
        self.thread.start()

    def write(self, template, params):
        try:
            self.queue.add({"template": template, "params": params})
            return self
        except Exception as e:
            raise e  # OH NO!

    def stop(self):
        try:
            self.queue.add(THREAD_STOP)  # BE PATIENT, LET REST OF MESSAGE BE SENT
            self.thread.join()
        except Exception as e:
            if DEBUG_LOGGING:
                raise e

        try:
            self.queue.close()
        except Exception as f:
            if DEBUG_LOGGING:
                raise f


def time_delta_pusher(please_stop, appender, queue, interval):
    """
    appender - THE FUNCTION THAT ACCEPTS A STRING
    queue - FILLED WITH LOG ENTRIES {"template":template, "params":params} TO WRITE
    interval - timedelta
    USE IN A THREAD TO BATCH LOGS BY TIME INTERVAL
    """

    next_run = time() + interval

    while not please_stop:
        profiler = Thread.current().cprofiler
        profiler.disable()
        (Till(till=next_run) | please_stop).wait()
        profiler.enable()

        next_run = time() + interval
        logs = queue.pop_all()
        if not logs:
            continue

        lines = []
        for log in logs:
            try:
                if log is THREAD_STOP:
                    please_stop.go()
                    next_run = time()
                else:
                    expanded = expand_template(log.get("template"), log.get("params"))
                    lines.append(expanded)
            except Exception as e:
                location = log.get('params', {}).get('location', {})
                Log.warning("Trouble formatting log from {{location}}", location=location, cause=e)
                # SWALLOW ERROR, GOT TO KEEP RUNNING
        try:
            appender(CR.join(lines) + CR)
        except Exception as e:

            sys.stderr.write(str("Trouble with appender: ") + str(e.__class__.__name__) + str(CR))
            # SWALLOW ERROR, MUST KEEP RUNNING


