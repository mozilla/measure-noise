# encoding: utf-8
#

from flask.sessions import SessionInterface as FlaskSessionInterface

from mo_dots import Data, wrap, exists, is_data
from mo_future import first
from mo_json import json2value, value2json
from mo_kwargs import override
from mo_logs import Log
from mo_math import bytes2base64URL, crypto
from mo_threads import Till
from mo_threads.threads import register_thread, Thread
from mo_times import Date
from mo_times.dates import parse, RFC1123, unix2Date
from pyLibrary.sql import SQL_WHERE, sql_list, SQL_SET, SQL_UPDATE
from pyLibrary.sql.sqlite import (
    sql_create,
    sql_eq,
    quote_column,
    sql_query,
    sql_insert,
    Sqlite,
    sql_lt,
)

DEBUG = False


def generate_sid():
    """
    GENERATE A UNIQUE SESSION ID
    """
    return bytes2base64URL(crypto.bytes(32))


SINGLTON = None


class SqliteSessionInterface(FlaskSessionInterface):
    """STORE SESSION DATA IN SQLITE

    :param db: Sqlite database
    :param table: The table name you want to use.
    :param use_signer: Whether to sign the session id cookie or not.
    """

    @override
    def __init__(self, flask_app, db, cookie, table="sessions"):
        global SINGLTON
        if SINGLTON:
            Log.error("Can only handle one session manager at a time")
        SINGLTON = self
        if is_data(db):
            self.db = Sqlite(db)
        else:
            self.db = db
        self.table = table
        self.cookie = cookie
        self.cookie.max_lifetime = parse(self.cookie.max_lifetime)
        self.cookie.inactive_lifetime = parse(self.cookie.inactive_lifetime)

        if not self.db.about(self.table):
            self.setup()
        Thread.run("session monitor", self.monitor)

    def create_session(self, session):
        session.session_id = generate_sid()
        session.permanent = True
        session.expires = (Date.now() + self.cookie.max_lifetime).unix

    def monitor(self, please_stop):
        while not please_stop:
            # Delete expired session
            try:
                with self.db.transaction() as t:
                    t.execute(
                        "DELETE FROM "
                        + quote_column(self.table)
                        + SQL_WHERE
                        + sql_lt(expires=Date.now().unix)
                    )
            except Exception as e:
                Log.warning("problem with session expires", cause=e)
            (please_stop | Till(seconds=60)).wait()

    def setup(self):
        with self.db.transaction() as t:
            t.execute(
                sql_create(
                    self.table,
                    {
                        "session_id": "TEXT PRIMARY KEY",
                        "data": "TEXT",
                        "last_used": "NUMBER",
                        "expires": "NUMBER",
                    },
                )
            )

    def cookie_data(self, session):
        return {
            "session_id": session.session_id,
            "expires": session.expires,
            "inactive_lifetime": self.cookie.inactive_lifetime.seconds,
        }

    def update_session(self, session_id, props):
        """
        UPDATE GIVEN SESSION WITH PROPERTIES
        :param session_id:
        :param props:
        :return:
        """
        now = Date.now().unix
        session = self.get_session(session_id)
        for k, v in props.items():
            session[k] = v
        session.last_used = now

        record = {
            "session_id": session_id,
            "data": value2json(session),
            "expires": session.expires,
            "last_used": session.last_used,
        }

        with self.db.transaction() as t:
            t.execute(
                SQL_UPDATE
                + quote_column(self.table)
                + SQL_SET
                + sql_list(sql_eq(**{k: v}) for k, v in record.items())
                + SQL_WHERE
                + sql_eq(session_id=session_id)
            )

    def get_session(self, session_id):
        now = Date.now().unix
        result = self.db.query(
            sql_query({"from": self.table, "where": {"eq": {"session_id": session_id}}})
        )
        saved_record = first(Data(zip(result.header, r)) for r in result.data)
        if not saved_record or saved_record.expires <= now:
            return Data()
        session = json2value(saved_record.data)

        DEBUG and Log.note("record from db {{session}}", session=saved_record)
        return session

    @register_thread
    def open_session(self, app, request):
        session_id = request.headers.get("Authorization")
        DEBUG and Log.note("got session_id {{session|quote}}", session=session_id)
        if not session_id:
            return Data()
        return self.get_session(session_id)

    @register_thread
    def save_session(self, app, session, response):
        if not session or not session.keys():
            return
        if not session.session_id:
            session.session_id = generate_sid()
            session.permanent = True
        DEBUG and Log.note("save session {{session}}", session=session)

        now = Date.now().unix
        session_id = session.session_id
        result = self.db.query(
            sql_query({"from": self.table, "where": {"eq": {"session_id": session_id}}})
        )
        saved_record = first(Data(zip(result.header, r)) for r in result.data)
        expires = min(session.expires, now + self.cookie.inactive_lifetime.seconds)
        if saved_record:
            DEBUG and Log.note("found session {{session}}", session=saved_record)

            saved_record.data = value2json(session)
            saved_record.expires = expires
            saved_record.last_used = now
            with self.db.transaction() as t:
                t.execute(
                    "UPDATE "
                    + quote_column(self.table)
                    + SQL_SET
                    + sql_list(sql_eq(**{k: v}) for k, v in saved_record.items())
                    + SQL_WHERE
                    + sql_eq(session_id=session_id)
                )
        else:
            new_record = {
                "session_id": session_id,
                "data": value2json(session),
                "expires": expires,
                "last_used": now,
            }
            DEBUG and Log.note("new record for db {{session}}", session=new_record)
            with self.db.transaction() as t:
                t.execute(sql_insert(self.table, new_record))


def setup_flask_session(flask_app, session_config):
    """
    SETUP FlASK SESSION MANAGEMENT
    :param flask_app: USED TO SET THE flask_app.config
    :param session_config: CONFIGURATION
    :return: THE SESSION MANAGER
    """
    session_config = wrap(session_config)
    output = flask_app.session_interface = SqliteSessionInterface(
        flask_app, kwargs=session_config
    )
    return output
