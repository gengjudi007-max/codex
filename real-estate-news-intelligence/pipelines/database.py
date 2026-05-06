import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'real_estate_news.db'
SCHEMA_PATH = BASE_DIR / 'database' / 'sqlite_schema.sql'


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

    def initialize(self):
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema = f.read()

        self.conn.executescript(schema)
        self.conn.commit()

    def execute(self, query, params=None):
        cursor = self.conn.cursor()
        cursor.execute(query, params or [])
        self.conn.commit()
        return cursor

    def fetchall(self, query, params=None):
        cursor = self.conn.cursor()
        cursor.execute(query, params or [])
        return cursor.fetchall()
