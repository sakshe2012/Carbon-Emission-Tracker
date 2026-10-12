import pymysql
import pymysql.cursors
# pyrefly: ignore [missing-import]
from flask import g, current_app

class Cursors:
    DictCursor = pymysql.cursors.DictCursor
    Cursor = pymysql.cursors.Cursor
    SSCursor = pymysql.cursors.SSCursor
    SSDictCursor = pymysql.cursors.SSDictCursor

cursors = Cursors

class MySQL(object):
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the `app` for use with this
        :class:`~flask_mysqldb.MySQL` class.
        """
        app.config.setdefault("MYSQL_HOST", "localhost")
        app.config.setdefault("MYSQL_USER", None)
        app.config.setdefault("MYSQL_PASSWORD", None)
        app.config.setdefault("MYSQL_DB", None)
        app.config.setdefault("MYSQL_PORT", 3306)
        app.config.setdefault("MYSQL_UNIX_SOCKET", None)
        app.config.setdefault("MYSQL_CONNECT_TIMEOUT", 10)
        app.config.setdefault("MYSQL_USE_UNICODE", True)
        app.config.setdefault("MYSQL_CHARSET", "utf8")
        app.config.setdefault("MYSQL_CURSORCLASS", None)
        app.config.setdefault("MYSQL_AUTOCOMMIT", False)

        if hasattr(app, "teardown_appcontext"):
            app.teardown_appcontext(self.teardown)

    @property
    def connect(self):
        kwargs = {}

        if current_app.config.get("MYSQL_HOST"):
            kwargs["host"] = current_app.config["MYSQL_HOST"]

        if current_app.config.get("MYSQL_USER"):
            kwargs["user"] = current_app.config["MYSQL_USER"]

        if current_app.config.get("MYSQL_PASSWORD"):
            kwargs["password"] = current_app.config["MYSQL_PASSWORD"]

        if current_app.config.get("MYSQL_DB"):
            kwargs["database"] = current_app.config["MYSQL_DB"]

        if current_app.config.get("MYSQL_PORT"):
            kwargs["port"] = int(current_app.config["MYSQL_PORT"])

        if current_app.config.get("MYSQL_UNIX_SOCKET"):
            kwargs["unix_socket"] = current_app.config["MYSQL_UNIX_SOCKET"]

        if current_app.config.get("MYSQL_CONNECT_TIMEOUT"):
            kwargs["connect_timeout"] = current_app.config["MYSQL_CONNECT_TIMEOUT"]

        if current_app.config.get("MYSQL_USE_UNICODE"):
            kwargs["use_unicode"] = current_app.config["MYSQL_USE_UNICODE"]

        if current_app.config.get("MYSQL_CHARSET"):
            kwargs["charset"] = current_app.config["MYSQL_CHARSET"]

        if current_app.config.get("MYSQL_CURSORCLASS"):
            cursor_class_name = current_app.config["MYSQL_CURSORCLASS"]
            kwargs["cursorclass"] = getattr(pymysql.cursors, cursor_class_name)

        if current_app.config.get("MYSQL_AUTOCOMMIT"):
            kwargs["autocommit"] = current_app.config["MYSQL_AUTOCOMMIT"]

        return pymysql.connect(**kwargs)

    @property
    def connection(self):
        """Attempts to connect to the MySQL server.

        :return: Bound MySQL connection object if successful or ``None`` if
            unsuccessful.
        """
        if not hasattr(g, "mysql_db"):
            g.mysql_db = self.connect
        return g.mysql_db

    def teardown(self, exception):
        if hasattr(g, "mysql_db"):
            g.mysql_db.close()
