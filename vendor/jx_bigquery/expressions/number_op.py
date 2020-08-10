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



from jx_base.expressions import NumberOp as NumberOp_
from jx_bigquery.expressions import _utils
from jx_bigquery.expressions._utils import BQLang, check
from jx_bigquery.expressions.bql_script import BQLScript
from jx_bigquery.sql import sql_call, ConcatSQL, SQL_AS, SQL_FLOAT64
from mo_imports import export
from mo_json import same_json_type, NUMBER


class NumberOp(NumberOp_):
    @check
    def to_bq(self, schema, not_null=False, boolean=False):
        value = BQLang[self.term].to_bq(schema)

        if same_json_type(value.data_type, NUMBER):
            return value
        else:
            return BQLScript(
                data_type=NUMBER,
                expr=sql_call("CAST", ConcatSQL(value, SQL_AS, SQL_FLOAT64)),
                frum=self,
                miss=self.missing(),
                many=False,
                schema=schema
            )


export("jx_bigquery.expressions._utils", NumberOp)
