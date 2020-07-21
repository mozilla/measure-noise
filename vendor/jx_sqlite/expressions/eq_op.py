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

from jx_base.expressions import (
    EqOp as EqOp_,
    FALSE,
    TRUE,
    ZERO,
    simplified,
)
from jx_base.expressions._utils import builtin_ops
from jx_sqlite.expressions._utils import SQLang, check
from jx_sqlite.expressions.case_op import CaseOp
from jx_sqlite.expressions.literal import Literal
from jx_sqlite.expressions.sql_eq_op import SqlEqOp
from jx_sqlite.expressions.sql_script import SQLScript
from jx_sqlite.expressions.when_op import WhenOp
from mo_json import BOOLEAN
from mo_logs import Log
from jx_sqlite.sqlite import SQL_FALSE, SQL_IS_NULL, SQL_OR, sql_iso, SQL_EQ


class EqOp(EqOp_):
    @check
    def to_sql(self, schema, not_null=False, boolean=False):
        lhs = SQLang[self.lhs].to_sql(schema)
        rhs = SQLang[self.rhs].to_sql(schema)
        acc = []
        if len(lhs) != len(rhs):
            Log.error("lhs and rhs have different dimensionality!?")

        for l, r in zip(lhs, rhs):
            for t in "bsnj":
                if l.sql[t] == None:
                    if r.sql[t] == None:
                        pass
                    else:
                        acc.append(sql_iso(r.sql[t]) + SQL_IS_NULL)
                elif l.sql[t] is ZERO:
                    if r.sql[t] == None:
                        acc.append(SQL_FALSE)
                    elif r.sql[t] is ZERO:
                        Log.error(
                            "Expecting expression to have been simplified already"
                        )
                    else:
                        acc.append(r.sql[t])
                else:
                    if r.sql[t] == None:
                        acc.append(sql_iso(l.sql[t]) + SQL_IS_NULL)
                    elif r.sql[t] is ZERO:
                        acc.append(l.sql[t])
                    else:
                        acc.append(sql_iso(l.sql[t]) + SQL_EQ + sql_iso(r.sql[t]))
        if not acc:
            return FALSE.to_sql(schema)
        else:
            return SQLScript(
                expr=SQL_OR.join(acc),
                frum=self,
                data_type=BOOLEAN,
                miss=FALSE,
                schema=schema,
            )

    @simplified
    def partial_eval(self):
        lhs = self.lhs.partial_eval()
        rhs = self.rhs.partial_eval()

        if isinstance(lhs, Literal) and isinstance(rhs, Literal):
            return TRUE if builtin_ops["eq"](lhs.value, rhs.value) else FALSE
        else:
            rhs_missing = rhs.missing().partial_eval()
            output = self.lang[CaseOp(
                [
                    WhenOp(lhs.missing(), **{"then": rhs_missing}),
                    WhenOp(rhs_missing, **{"then": FALSE}),
                    SqlEqOp([lhs, rhs]),
                ]
            )].partial_eval()
            return output
