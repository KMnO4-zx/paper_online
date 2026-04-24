#!/usr/bin/env bash
set -euo pipefail

DATABASE_URL="$(python scripts/config_value.py database.url)"
if [[ -z "${DATABASE_URL}" ]]; then
  echo "Error: database.url is not set in config.yaml." >&2
  exit 1
fi

DUMP_FILE="${DUMP_FILE:-db/dumps/supabase_data.dump}"
PG_RESTORE_BIN="${PG_RESTORE_BIN:-pg_restore}"
PSQL_BIN="${PSQL_BIN:-psql}"

if [[ ! -f "${DUMP_FILE}" ]]; then
  echo "Error: dump file not found: ${DUMP_FILE}" >&2
  exit 1
fi

tmp_sql="$(mktemp "${TMPDIR:-/tmp}/paper-online-public-data.XXXXXX.sql")"
cleanup() {
  rm -f "${tmp_sql}"
}
trap cleanup EXIT

"${PG_RESTORE_BIN}" \
  --data-only \
  --no-owner \
  --no-privileges \
  --schema=public \
  --file "${tmp_sql}" \
  "${DUMP_FILE}"

# PostgreSQL 17 pg_dump emits transaction_timeout, but PostgreSQL 16 does not
# understand it. Removing this keeps restores compatible with the current
# local/self-hosted target version.
sed -i.bak '/^SET transaction_timeout = 0;$/d' "${tmp_sql}"
rm -f "${tmp_sql}.bak"

"${PSQL_BIN}" "${DATABASE_URL}" --set ON_ERROR_STOP=1 --single-transaction -f "${tmp_sql}"

echo "Restored public data from ${DUMP_FILE} into ${DATABASE_URL}"
