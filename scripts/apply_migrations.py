#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

import psycopg

repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "backend"))

from config import settings
from migrations import apply_migrations

DATABASE_URL = settings.database.url
SEEDS_DIR = repo_root / "db" / "seeds"


def apply_sql_file(conn: psycopg.Connection, sql_file: Path) -> None:
    sql = sql_file.read_text(encoding="utf-8")
    if not sql.strip():
        return

    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print(f"Applied {sql_file.relative_to(repo_root)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply PostgreSQL migrations for Paper Insight")
    parser.add_argument(
        "--seed",
        choices=["dev"],
        help="Optionally apply a bundled seed after migrations",
    )
    args = parser.parse_args()

    if not DATABASE_URL:
        print("Error: database.url not found in config.yaml", file=sys.stderr)
        return 1

    apply_migrations()
    with psycopg.connect(DATABASE_URL) as conn:
        if args.seed == "dev":
            apply_sql_file(conn, SEEDS_DIR / "dev_seed.sql")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
