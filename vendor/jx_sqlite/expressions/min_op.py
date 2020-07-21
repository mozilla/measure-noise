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

from jx_base.expressions import MinOp as MinOp_
from jx_sqlite.expressions._utils import SQLang, check
from mo_dots import wrap
from jx_sqlite.sqlite import sql_iso, sql_list


class MinOp(MinOp_):
    @check
    def to_sql(self, schema, not_null=False, boolean=False):
        terms = [SQLang[t].partial_eval().to_sql(schema)[0].sql.n for t in self.terms]
        return wrap([{"name": ".", "sql": {"n": "min" + sql_iso((sql_list(terms)))}}])
