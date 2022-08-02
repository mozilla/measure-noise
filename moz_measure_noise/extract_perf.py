# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Perftest Team (perftest@mozilla.com)
#
from __future__ import absolute_import, division, unicode_literals

from jx_mysql.mysql import quote_list, MySQL, quote_value
from mo_dots import listwrap
from mo_future import first
from mo_sql import SQL


def get_all_signatures(db_config, sql):
    """
    RETURN ALL SIGNATURES FROM PERFHERDER DATABASE
    """
    db = MySQL(db_config)
    with db:
        return db.query(sql)


def get_signature(db_config, signature_id):
    db = MySQL(db_config)
    with db:
        return first(
            db.query(f"""
                SELECT
                    t1.id , 
                    t1.signature_hash, 
                    t1.suite ,
                    t1.test ,
                    UNIX_TIMESTAMP(t1.last_updated) as last_updated,
                    t1.lower_is_better,
                    t1.has_subtests ,
                    t1.alert_threshold,
                    t1.fore_window ,
                    t1.max_back_window,
                    t1.min_back_window ,
                    t1.should_alert, 
                    t1.extra_options ,
                    t1.alert_change_type,
                    t1.measurement_unit,
                    t1.application ,
                    t1.suite_public_name,
                    t1.test_public_name ,
                    t1.tags,
                    t3.option_collection_hash as `option_collection.hash`,
                    t1.framework_id,
                    t4.name AS framework, 
                    t5.platform AS platform, 
                    t6.name AS `repository`
                FROM
                    performance_signature t1
                LEFT JOIN
                    performance_signature AS t2 ON t2.id = t1.parent_signature_id
                LEFT JOIN
                    option_collection AS t3 ON t3.id = t1.option_collection_id
                LEFT JOIN
                    performance_framework AS t4 ON t4.id = t1.framework_id
                LEFT JOIN
                    machine_platform AS t5 ON t5.id = t1.platform_id
                LEFT JOIN
                   repository AS t6 ON t6.id = t1.repository_id
                WHERE
                    t1.id in {quote_list(listwrap(signature_id))}
                ORDER BY 
                    t1.last_updated DESC
            """)
        )


def get_dataum(db_config, signature_id, since, limit):
    db = MySQL(db_config)
    with db:
        return db.query(
            SQL(
                f"""
        SELECT
            d.id,
            d.value,
            t3.id AS `job.id`,
            t3.guid AS `job.guid`,
            p.revision AS `push.revision`,
            UNIX_TIMESTAMP(p.time) AS `push.time`,
            r.name AS `push.repository`,
            s.created AS `summary.created`,
            s.status AS `summary.status`,
            s.bug_number AS `summary.bug_number`,
            s.manually_created AS `summary.manually_created`,
            s.prev_push_id AS `summary.prev_push`,
            s.issue_tracker_id AS `summary.issue_tracker`,
            s.notes AS `summary.notes`,
            s.first_triaged AS `summary.first_triaged`,
            s.last_updated AS `summary.last_updated`,
            s.bug_updated AS `summary.bug_updated`,
            a.id AS `alert.id`,
            a.`is_regression` AS `alert.isregression`,
            a.`status` AS `alert.status`,
            a.`amount_pct` AS `alert.amount_pct`,
            a.`amount_abs` AS `alert.amount_abs`,
            a.`prev_value` AS `alert.prev_value`,
            a.`new_value` AS `alert.new_value`,
            a.`t_value` AS `alert.t_value`,
            a.`manually_created` AS `alert.manually_created`,
            a.`classifier_id` AS `alert.classifier_id`,
            a.`starred` AS `alert.starred`,
            a.`created` AS `alert.created`,
            a.`first_triaged` AS `alert.first_triaged`,
            a.`last_updated` AS `alert.last_updated`
        FROM
            performance_datum AS d
        JOIN 
            performance_signature sig on sig.id=d.signature_id
        LEFT JOIN
            job AS t3 ON t3.id = d.job_id
        LEFT JOIN
            push AS p ON p.id = d.push_id
        LEFT JOIN
            repository AS r ON r.id = p.repository_id
        LEFT JOIN
            performance_alert_summary s on s.repository_id = p.repository_id and s.push_id=p.id
        LEFT JOIN
            performance_alert a 
        ON 
            a.summary_id = s.id AND 
            a.series_signature_id = d.signature_id AND 
            a.manually_created=0
        WHERE
            p.time > {quote_value(since)} AND
            d.signature_id in {quote_list(listwrap(signature_id))}
        ORDER BY
            p.time DESC
        LIMIT
            {quote_value(limit + 1)}
        """
            )
        )
