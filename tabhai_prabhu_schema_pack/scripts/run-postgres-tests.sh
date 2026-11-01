#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${DATABASE_URL:?Set DATABASE_URL to a disposable LOCAL PostgreSQL 17 database}"

psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$ROOT/001_scripture_schema_draft.sql"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$ROOT/002_search_indexes_draft.sql"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$ROOT/004_seed_work_catalog_draft.sql"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$ROOT/003_schema_invariants_test.sql"

echo "PostgreSQL schema validation passed. Use a disposable local database only."
