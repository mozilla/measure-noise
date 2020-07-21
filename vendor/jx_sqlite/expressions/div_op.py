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

from jx_base.expressions import DivOp as DivOp_
from jx_sqlite.expressions._utils import SQLang, check
from mo_dots import Null, wrap
from jx_sqlite.sqlite import sql_coalesce, sql_iso


class DivOp(DivOp_):
    @check
    def to_sql(self, schema, not_null=False, boolean=False):
        lhs = SQLang[self.lhs].to_sql(schema)[0].sql.n
        rhs = SQLang[self.rhs].to_sql(schema)[0].sql.n
        d = SQLang[self.default].to_sql(schema)[0].sql.n

        if lhs and rhs:
            if d == None:
                return wrap(
                    [{"name": ".", "sql": {"n": sql_iso(lhs) + " / " + sql_iso(rhs)}}]
                )
            else:
                return wrap(
                    [
                        {
                            "name": ".",
                            "sql": {
                                "n": sql_coalesce(
                                    [sql_iso(lhs) + " / " + sql_iso(rhs), d]
                                )
                            },
                        }
                    ]
                )
        else:
            return Null
