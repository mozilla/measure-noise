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

from jx_base.expressions import AbsOp as AbsOp_, TRUE
from jx_sqlite.expressions._utils import SQLang, check
from jx_sqlite.expressions.sql_script import SQLScript
from jx_sqlite.sqlite import sql_call
from mo_json import NUMBER, IS_NULL
from mo_sql import SQL_NULL


class AbsOp(AbsOp_):
    @check
    def to_sql(self, schema, not_null=False, boolean=False):
        expr = SQLang[self.term].partial_eval().to_sql(schema)[0].sql.n
        if not expr:
            return SQLScript(
                expr=SQL_NULL,
                data_type=IS_NULL,
                frum=self,
                miss=TRUE,
                schema=schema,
            )

        return SQLScript(
            expr=sql_call("ABS", expr),
            data_type=NUMBER,
            frum=self,
            miss=self.missing(),
            schema=schema,
        )
