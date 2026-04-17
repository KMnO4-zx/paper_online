#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

repo_root = Path(__file__).parent.parent
load_dotenv(repo_root / "backend" / ".env")
load_dotenv(repo_root / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
MIGRATIONS_DIR = repo_root / "db" / "migrations"
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
        print("Error: DATABASE_URL not found in environment variables", file=sys.stderr)
        return 1

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        print("Error: no migration files found", file=sys.stderr)
        return 1

    with psycopg.connect(DATABASE_URL) as conn:
        for migration_file in migration_files:
            apply_sql_file(conn, migration_file)

        if args.seed == "dev":
            apply_sql_file(conn, SEEDS_DIR / "dev_seed.sql")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
