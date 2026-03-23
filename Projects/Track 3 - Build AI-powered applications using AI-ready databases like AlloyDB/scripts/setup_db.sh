#!/usr/bin/env bash
set -euo pipefail

: "${DB_HOST:?Set DB_HOST}"
: "${DB_PORT:=5432}"
: "${DB_NAME:=postgres}"
: "${DB_USER:?Set DB_USER}"
: "${DB_PASSWORD:?Set DB_PASSWORD}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export PGPASSWORD="${DB_PASSWORD}"

psql "host=${DB_HOST} port=${DB_PORT} dbname=${DB_NAME} user=${DB_USER} sslmode=require" \
  -f "${ROOT_DIR}/sql/01_schema.sql"

psql "host=${DB_HOST} port=${DB_PORT} dbname=${DB_NAME} user=${DB_USER} sslmode=require" \
  -f "${ROOT_DIR}/sql/03_nl_config.sql"

echo "Database setup completed."
