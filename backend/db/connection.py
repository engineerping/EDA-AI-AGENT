import os
import psycopg2
from contextlib import contextmanager

DB_URL = os.environ.get("EDB_PG_URL", "postgresql://postgres:password@localhost:5432/eda_agent")

@contextmanager
def get_connection():
    conn = psycopg2.connect(DB_URL)
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def get_cursor():
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()