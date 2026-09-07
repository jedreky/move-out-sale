import json
import sqlite3
from pathlib import Path

DB_PATH = Path("data/sqlite.db")


def dump(conn: sqlite3.Connection) -> dict:
    conn.row_factory = sqlite3.Row

    tables = [
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    ]

    schema = {}
    for table in tables:
        cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
        fks = conn.execute(f"PRAGMA foreign_key_list({table})").fetchall()
        schema[table] = {
            "columns": [dict(c) for c in cols],
            "foreign_keys": [dict(fk) for fk in fks],
        }

    data = {table: [dict(row) for row in conn.execute(f"SELECT * FROM {table}")] for table in tables}

    return {"schema": schema, "data": data}


if __name__ == "__main__":
    with sqlite3.connect(DB_PATH) as conn:
        result = dump(conn)

    schema_path = Path("db_schema.json")
    data_path = Path("db_data.json")

    schema_path.write_text(json.dumps(result["schema"], indent=2))
    data_path.write_text(json.dumps(result["data"], indent=2))

    print(f"Schema written to {schema_path}")
    print(f"Data written to {data_path}")
    for table, rows in result["data"].items():
        print(f"  {table}: {len(rows)} rows")
