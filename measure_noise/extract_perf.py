from mo_dots import listwrap
from mo_future import text
from mo_logs.strings import expand_template
from pyLibrary.sql.mysql import MySQL, quote_list

from pyLibrary.sql import SQL

WORKLIST = SQL("""
    SELECT s.id 
    FROM performance_signature s
    WHERE
        -- s.id=2153028
        s.framework_id = 10 AND 
        (s.test IS NULL or s.test='' or s.test=s.suite) and
        s.repository_id = 77  AND -- autoland 
        s.repository_id <> 4  AND -- try
        s.repository_id <> 1  -- mozilla-central
    GROUP BY s.id 
    -- ORDER BY s.last_updated DESC
    -- LIMIT 1
""")

def get_worklist(db_config):
    db = MySQL(db_config)
    with db:
        return db.query(text(WORKLIST))


def get_signature(db_config, signature_id):
    db = MySQL(db_config)
    with db:
        return db.query(expand_template(signature_sql, quote_list(listwrap(signature_id))))


def get_dataum(db_config, signature_id):
    db = MySQL(db_config)
    with db:
        return db.query(expand_template(datum_sql, quote_list(listwrap(signature_id))))


signature_sql = """
    SELECT
        t1.id , 
        t1.signature_hash , 
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
        t4.name AS framework, 
        t5.platform AS platform, 
        t6.name AS `repository.name`
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
        t1.id IN {{signature}} 
"""


datum_sql = """
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
            a.`amount_abs` AS `alert.anount_abs`,
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
        LEFT JOIN
            job AS t3 ON t3.id = d.job_id
        LEFT JOIN
            push AS p ON p.id = d.push_id
        LEFT JOIN
            repository AS r ON r.id = p.repository_id
        LEFT JOIN
            performance_alert_summary s on s.repository_id = p.repository_id and s.push_id=p.id
        LEFT JOIN
            performance_alert a on a.summary_id = s.id AND a.series_signature_id = d.signature_id AND a.manually_created=0
        WHERE
            p.time > DATE_ADD(DATE(NOW()), INTERVAL -3 MONTH) AND
            d.signature_id in {{signature}}
        ORDER BY
            p.time DESC
    """
