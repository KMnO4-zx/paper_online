#!/usr/bin/env bash
set -euo pipefail

if ! command -v pg_dump >/dev/null 2>&1; then
  echo "Error: pg_dump is required. Install PostgreSQL client tools first." >&2
  exit 1
fi

if [[ -z "${SUPABASE_DATABASE_URL:-}" ]]; then
  echo "Error: SUPABASE_DATABASE_URL is not set." >&2
  exit 1
fi

PG_DUMP_BIN="${PG_DUMP_BIN:-pg_dump}"

mkdir -p db/dumps

${PG_DUMP_BIN} "${SUPABASE_DATABASE_URL}" \
  --schema=public \
  --schema-only \
  --no-owner \
  --no-privileges \
  --file db/dumps/supabase_schema.sql

${PG_DUMP_BIN} "${SUPABASE_DATABASE_URL}" \
  --schema=public \
  --data-only \
  --format=custom \
  --no-owner \
  --no-privileges \
  --file db/dumps/supabase_data.dump

echo "Exported public schema to db/dumps/supabase_schema.sql"
echo "Exported public data to db/dumps/supabase_data.dump"
