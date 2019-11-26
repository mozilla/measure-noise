from mo_dots import wrap, Data, listwrap, is_data, FlatList
from mo_future import first
from mo_kwargs import override
from mo_logs import Log
from pyLibrary.sql import SQL_UPDATE, SQL_SET
from pyLibrary.sql.sqlite import sql_query, sql_create, sql_insert, quote_column, sql_eq, Sqlite

ROOT_USER = wrap({"_id": 1})
VERSION_TABLE = "security.version"
GROUP_TABLE = "security.groups"
PERMISSION_TABLE = "security.permissions"
RESOURCE_TABLE = "security.resources"
TABLE_OPERATIONS = ["insert", "update", "from"]
CREATE_TABLE = {"_id": 100, "table": ".", "operation": "insert", "owner": 1}


class Permissions:
    @override
    def __init__(self, db, kwargs):
        if is_data(db):
            self.db = Sqlite(db)
        elif isinstance(db, Sqlite):
            self.db = db
        else:
            Log.error("Bad db parameter")

        if not self.db.about(PERMISSION_TABLE):
            self.setup()
        self.next_id = id_generator(self.db)

    def setup(self):
        with self.db.transaction() as t:
            t.execute(sql_create(VERSION_TABLE, {"version": "TEXT"}))
            t.execute(sql_insert(VERSION_TABLE, {"version": "1.0"}))

            t.execute(
                sql_create(
                    GROUP_TABLE,
                    {
                        "_id": "LONG PRIMARY KEY",
                        "name": "TEXT",
                        "group": "TEXT",
                        "email": "TEXT",
                        "issuer": "TEXT",
                        "email_verified": "INTEGER",
                        "description": "TEXT",
                        "owner": "LONG",
                    },
                )
            )

            t.execute(
                sql_insert(
                    GROUP_TABLE,
                    [
                        {
                            "_id": 1,
                            "name": "root",
                            "email": "nobody@mozilla.com",
                            "description": "access for security system",
                        },
                        {
                            "_id": 11,
                            "group": "public",
                            "description": "everyone with confirmed email",
                            "owner": 1,
                        },
                        {
                            "_id": 12,
                            "group": "mozillians",
                            "description": "people that mozilla authentication has recongized as mozillian",
                            "owner": 1,
                        },
                        {
                            "_id": 13,
                            "group": "moz-employee",
                            "description": "people that mozilla authentication has recongized as employee",
                            "owner": 1,
                        },
                    ],
                )
            )

            t.execute(
                sql_create(
                    RESOURCE_TABLE,
                    {
                        "_id": "LONG PRIMARY KEY",
                        "table": "TEXT",
                        "operation": "TEXT",
                        "owner": "LONG",
                    },
                )
            )
            t.execute(
                sql_insert(
                    RESOURCE_TABLE,
                    [
                        CREATE_TABLE,
                        {"_id": 101, "table": ".", "operation": "update", "owner": 1},
                        {"_id": 102, "table": ".", "operation": "from", "owner": 1},
                    ],
                )
            )

            t.execute(
                sql_create(
                    PERMISSION_TABLE,
                    {"user": "LONG", "resource": "LONG", "owner": "LONG"},
                )
            )
            t.execute(
                sql_insert(
                    PERMISSION_TABLE,
                    [
                        {"user": 12, "resource": 11, "owner": 1},
                        {"user": 13, "resource": 11, "owner": 1},
                        {"user": 13, "resource": 12, "owner": 1},
                        {"user": 1, "resource": 100, "owner": 1},
                        {"user": 1, "resource": 101, "owner": 1},
                        {"user": 1, "resource": 102, "owner": 1},
                    ],
                )
            )

    def create_table_resource(self, table_name, owner):
        """
        CREATE A TABLE, CREATE RESOURCES FOR OPERATIONS, ENSURE CREATOR HAS CONTROL OVER TABLE

        :param table_name:  Create resources for given table
        :param owner: assign this user as owner
        :return:
        """
        new_resources = wrap(
            [
                {"table": table_name, "operation": op, "owner": 1}
                for op in TABLE_OPERATIONS
            ]
        )
        self._insert(RESOURCE_TABLE, new_resources)



        with self.db.transaction() as t:
            t.execute(sql_insert(
                PERMISSION_TABLE,
                [
                    {"user": owner._id, "resource": r._id, "owner": ROOT_USER._id}
                    for r in new_resources
                ]
            ))

    def get_or_create_user(self, details):
        details = wrap(details)
        issuer = details.sub or details.issuer
        email = details.email
        email_verified = details.email_verified
        if not email:
            Log.error("Expecting id_token to have claims.email propert")

        result = self.db.query(
            sql_query(
                {
                    "select": ["_id", "email", "issuer"],
                    "from": GROUP_TABLE,
                    "where": {"eq": {"email": email, "issuer": issuer}},
                }
            )
        )

        if result.data:
            user = Data(zip(result.header, first(result.data)))
            user.email_verified = email_verified
            return user

        new_user = wrap({
            "email": email,
            "issuer": issuer,
            "email_verified": email_verified,
            "owner": ROOT_USER._id
        })
        self._insert(GROUP_TABLE, new_user)
        return new_user

    def get_resource(self, table, operation):
        result = self.db.query(
            sql_query(
                {
                    "select": "_id",
                    "from": RESOURCE_TABLE,
                    "where": {"eq": {"table": table, "operation": operation}},
                }
            )
        )
        if not result.data:
            Log.error("Expecting to find a resource")

        return Data(zip(result.header, first(result.data)))

    def add_permission(self, user, resource, owner):
        """
        :param user:
        :param resource:
        :param owner:
        :return:
        """
        user = wrap(user)
        resource = wrap(resource)
        owner = wrap(owner)

        # DOES owner HAVE ACCESS TO resource?
        if not self.verify_allowance(owner, resource):
            Log.error("not allowed to assign resource")

        # DOES THIS PERMISSION EXIST ALREADY
        allowance = self.verify_allowance(user, resource)
        if allowance:
            if any(r.owner == owner for r in allowance):
                Log.error("already allowed via {{allowance}}", allowance=allowance)
            # ALREADY ALLOWED, BUT MULTIPLE PATHS MAY BE OK
        with self.db.transaction() as t:
            t.execute(sql_insert(PERMISSION_TABLE, {"user": user._id, "resource": resource._id, "owner": owner._id}))

    def verify_allowance(self, user, resource):
        """
        VERIFY IF user CAN ACCESS resource
        :param user:
        :param resource:
        :return: ALLOWANCE CHAIN
        """
        user = wrap(user)
        resource = wrap(resource)
        resources = self.db.query(
            sql_query(
                {
                    "select": ["resource", "owner"],
                    "from": PERMISSION_TABLE,
                    "where": {"eq": {"user": user._id}},
                }
            )
        )

        for r in resources.data:
            record = Data(zip(resources.header, r))
            if record.resource == resource._id:
                if record.owner == ROOT_USER._id:
                    return FlatList(vals=[{"resource": resource, "user": user, "owner": ROOT_USER}])
                else:
                    cascade = self.verify_allowance(
                        wrap({"_id": record.owner}), resource
                    )
                    if cascade:
                        cascade.append(
                            {"resource": resource, "user": user, "owner": record.owner}
                        )
                    return cascade
            else:
                group = record.resource
                cascade = self.verify_allowance(wrap({"_id": group}), resource)
                if cascade:
                    cascade.append(
                        {"group": group, "user": user, "owner": record.owner}
                    )
                    return cascade

        return []

    def find_resource(self, table, operation):
        result = self.db.query(
            sql_query(
                {
                    "from": RESOURCE_TABLE,
                    "where": {"eq": {"table": table, "operation": operation}}
                }
            )
        )

        return first(Data(zip(result.header, r)) for r in result.data)

    def _insert(self, table, records):
        records = listwrap(records)
        keys = {"_id"}
        for r in records:
            keys.update(r.keys())
            if r._id == None:
                r._id = self.next_id()

        with self.db.transaction() as t:
            t.execute(sql_insert(table, records))


def id_generator(db):
    """
    INSTALL AN ID GENERATOR
    """
    about = db.about(VERSION_TABLE)
    if not about:
        with db.transaction() as t:
            t.execute(sql_create(VERSION_TABLE, {"version": "TEXT", "next_id": "LONG"}))
            t.execute(sql_insert(VERSION_TABLE, {"version": "1.0", "next_id": 1000}))
    else:
        for cid, name, dtype, notnull, dfft_value, pk in about:
            if name == "next_id":
                break
        else:
            with db.transaction() as t:
                t.execute(
                    "ALTER TABLE "
                    + quote_column(VERSION_TABLE)
                    + " ADD COLUMN next_id LONG"
                )
                t.execute(
                    SQL_UPDATE
                    + quote_column(VERSION_TABLE)
                    + SQL_SET
                    + sql_eq(next_id=1000)
                )

    def _gen_ids():
        while True:
            with db.transaction() as t:
                top_id = first(
                    first(
                        t.query(
                            sql_query({"select": "next_id", "from": VERSION_TABLE})
                        ).data
                    )
                )
                max_id = top_id + 1000
                t.execute(
                    SQL_UPDATE
                    + quote_column(VERSION_TABLE)
                    + SQL_SET
                    + sql_eq(next_id=max_id)
                )
            while top_id < max_id:
                yield top_id
                top_id += 1

    return _gen_ids().__next__
