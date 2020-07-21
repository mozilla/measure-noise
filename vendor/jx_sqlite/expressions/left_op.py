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

from jx_base.expressions import LeftOp as LeftOp_, ONE
from jx_sqlite.expressions._utils import check
from jx_sqlite.expressions.sql_substr_op import SqlSubstrOp


class LeftOp(LeftOp_):
    @check
    def to_sql(self, schema, not_null=False, boolean=False):
        return SqlSubstrOp([self.value, ONE, self.length]).partial_eval().to_sql(schema)
