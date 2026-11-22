
import sqlite3

DEFAULT_DB_PATH = "heritage.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS traditions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    community   TEXT NOT NULL,
    description TEXT NOT NULL,
    created_by  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name  TEXT NOT NULL,
    event_date  TEXT NOT NULL,
    location    TEXT NOT NULL,
    created_by  TEXT NOT NULL
);
"""


class Database:

    def __init__(self, path=DEFAULT_DB_PATH):
        self.path = path
        self.conn = sqlite3.connect(path)
        try:
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.conn.executescript(SCHEMA)
            self.conn.commit()
        except sqlite3.Error:
            self.conn.close()
            raise

    def execute(self, sql, params=()):
        cursor = self.conn.execute(sql, params)
        try:
            self.conn.commit()
            return cursor
        except sqlite3.Error:
            cursor.close()
            raise

    def fetch_all(self, sql, params=()):
        cursor = self.conn.execute(sql, params)
        try:
            return cursor.fetchall()
        finally:
            cursor.close()

    def fetch_one(self, sql, params=()):
        cursor = self.conn.execute(sql, params)
        try:
            return cursor.fetchone()
        finally:
            cursor.close()

    def close(self):
        self.conn.close()
