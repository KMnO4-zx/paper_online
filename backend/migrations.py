import logging
from pathlib import Path

import psycopg

from config import REPO_ROOT, settings


logger = logging.getLogger(__name__)
MIGRATIONS_DIR = REPO_ROOT / "db" / "migrations"


def apply_migrations() -> None:
    if not settings.database.url:
        raise RuntimeError("database.url not found in config.yaml")

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        raise RuntimeError(f"no migration files found in {MIGRATIONS_DIR}")

    with psycopg.connect(settings.database.url) as conn:
        for migration_file in migration_files:
            sql = migration_file.read_text(encoding="utf-8")
            if not sql.strip():
                continue
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            logger.info("Applied migration %s", migration_file.relative_to(REPO_ROOT))
