# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import absolute_import, division, unicode_literals

from jx_base.expressions import CaseOp as CaseOp_
from jx_sqlite.expressions._utils import SQLang, check
from mo_dots import coalesce, wrap
from jx_sqlite.sqlite import (
    SQL_CASE,
    SQL_ELSE,
    SQL_END,
    SQL_NULL,
    SQL_THEN,
    SQL_WHEN,
    ConcatSQL,
)


class CaseOp(CaseOp_):
    @check
    def to_sql(self, schema, not_null=False, boolean=False):
        if len(self.whens) == 1:
            return SQLang[self.whens[-1]].to_sql(schema)

        output = {}
        for t in "bsn":  # EXPENSIVE LOOP to_sql() RUN 3 TIMES
            els_ = coalesce(SQLang[self.whens[-1]].to_sql(schema)[0].sql[t], SQL_NULL)
            acc = SQL_ELSE + els_ + SQL_END
            for w in reversed(self.whens[0:-1]):
                acc = ConcatSQL(
                    SQL_WHEN,
                    SQLang[w.when].to_sql(schema, boolean=True)[0].sql.b,
                    SQL_THEN,
                    coalesce(SQLang[w.then].to_sql(schema)[0].sql[t], SQL_NULL),
                    acc,
                )
            output[t] = SQL_CASE + acc
        return wrap([{"name": ".", "sql": output}])
