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

from jx_sqlite.sqlite import quote_value

from jx_base.expressions import StringOp as StringOp_
from jx_sqlite.expressions._utils import SQLang, check
from mo_dots import wrap
from jx_sqlite.sqlite import (
    SQL_CASE,
    SQL_ELSE,
    SQL_END,
    SQL_NULL,
    SQL_THEN,
    SQL_WHEN,
    sql_coalesce,
    sql_iso,
)


class StringOp(StringOp_):
    @check
    def to_sql(self, schema, not_null=False, boolean=False):
        test = SQLang[self.term].missing().to_sql(schema, boolean=True)[0].sql.b
        value = SQLang[self.term].to_sql(schema, not_null=True)[0].sql
        acc = []
        for t, v in value.items():
            if t == "b":
                acc.append(
                    SQL_CASE
                    + SQL_WHEN
                    + sql_iso(test)
                    + SQL_THEN
                    + SQL_NULL
                    + SQL_WHEN
                    + sql_iso(v)
                    + SQL_THEN
                    + "'true'"
                    + SQL_ELSE
                    + "'false'"
                    + SQL_END
                )
            elif t == "s":
                acc.append(v)
            else:
                acc.append(
                    "RTRIM(RTRIM(CAST"
                    + sql_iso(v + " as TEXT), " + quote_value("0"))
                    + ", "
                    + quote_value(".")
                    + ")"
                )
        if not acc:
            return wrap([{}])
        elif len(acc) == 1:
            return wrap([{"name": ".", "sql": {"s": acc[0]}}])
        else:
            return wrap([{"name": ".", "sql": {"s": sql_coalesce(acc)}}])
