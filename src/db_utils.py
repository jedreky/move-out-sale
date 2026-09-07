import sqlite3
from pathlib import Path

DB_PATH = Path("data/sqlite.db")


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                desc TEXT NOT NULL,
                price INTEGER NOT NULL,
                available_on TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'available'
            );
            CREATE TABLE IF NOT EXISTS pictures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                FOREIGN KEY (item_id) REFERENCES items (id)
            );
        """)


if __name__ == "__main__":
    init_db()
