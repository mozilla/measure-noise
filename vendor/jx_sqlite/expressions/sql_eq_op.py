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

from jx_base.expressions import FALSE, SqlEqOp as SqlEqOp_, is_literal
from jx_sqlite.expressions._utils import SQLang, check
from jx_sqlite.expressions.boolean_op import BooleanOp
from mo_dots import wrap
from mo_logs import Log
from jx_sqlite.sqlite import SQL_IS_NULL, SQL_OR, sql_iso, ConcatSQL, JoinSQL, SQL_EQ


class SqlEqOp(SqlEqOp_):
    @check
    def to_sql(self, schema, not_null=False, boolean=False):
        lhs = SQLang[self.lhs].partial_eval()
        rhs = SQLang[self.rhs].partial_eval()
        lhs_sql = lhs.to_sql(schema, not_null=True)
        rhs_sql = rhs.to_sql(schema, not_null=True)
        if is_literal(rhs) and lhs_sql[0].sql.b != None and rhs.value in ("T", "F"):
            rhs_sql = BooleanOp(rhs).to_sql(schema)
        if is_literal(lhs) and rhs_sql[0].sql.b != None and lhs.value in ("T", "F"):
            lhs_sql = BooleanOp(lhs).to_sql(schema)

        if len(lhs_sql) != len(rhs_sql):
            Log.error("lhs and rhs have different dimensionality!?")

        acc = []
        for l, r in zip(lhs_sql, rhs_sql):
            for t in "bsnj":
                if r.sql[t] == None:
                    if l.sql[t] == None:
                        pass
                    else:
                        acc.append(ConcatSQL(l.sql[t], SQL_IS_NULL))
                elif l.sql[t] == None:
                    acc.append(ConcatSQL(r.sql[t], SQL_IS_NULL))
                else:
                    acc.append(
                        ConcatSQL(sql_iso(l.sql[t]), SQL_EQ, sql_iso(r.sql[t]))
                    )
        if not acc:
            return FALSE.to_sql(schema)
        else:
            return wrap([{"name": ".", "sql": {"b": JoinSQL(SQL_OR, acc)}}])
