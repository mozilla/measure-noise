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

from jx_sqlite.sqlite import quote_list

from jx_base.expressions import InOp as InOp_
from jx_base.language import is_op
from jx_sqlite.expressions._utils import SQLang, check
from jx_sqlite.expressions.literal import Literal
from mo_dots import wrap
from mo_json import json2value
from mo_logs import Log
from jx_sqlite.sqlite import SQL_FALSE, SQL_OR, sql_iso, ConcatSQL, SQL_IN


class InOp(InOp_):
    @check
    def to_sql(self, schema, not_null=False, boolean=False):
        if not is_op(self.superset, Literal):
            Log.error("Not supported")
        j_value = json2value(self.superset.json)
        if j_value:
            var = SQLang[self.value].to_sql(schema)
            sql = SQL_OR.join(
                sql_iso(v, SQL_IN, quote_list(j_value))
                for t, v in var[0].sql.items()
            )
        else:
            sql = SQL_FALSE
        return wrap([{"name": ".", "sql": {"b": sql}}])
