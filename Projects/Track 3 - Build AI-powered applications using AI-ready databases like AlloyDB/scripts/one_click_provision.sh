#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || true)}"
REGION="${REGION:-asia-southeast2}"
SERVICE_NAME="${SERVICE_NAME:-alloydb-nl}"
AUTO_PROVISION="${AUTO_PROVISION:-}"
SEED_LIMIT="${SEED_LIMIT:-5000}"
APP_NL_TO_SQL_TEMPLATE="${APP_NL_TO_SQL_TEMPLATE:-select alloydb_ai_nl.get_sql('track3_cfg','{question}') ->> 'sql'}"
DEFAULT_DB_PASSWORD="@egsevx75FBXbUrW"

# If DB_HOST is already provided, default to existing-cluster mode.
if [[ -z "${AUTO_PROVISION}" ]]; then
  if [[ -n "${DB_HOST:-}" ]]; then
    AUTO_PROVISION="false"
  else
    AUTO_PROVISION="true"
  fi
fi

if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == "(unset)" ]]; then
  echo "PROJECT_ID is not set and no default gcloud project was found."
  echo "Set it first: export PROJECT_ID=your-project-id"
  exit 1
fi

if [[ "${AUTO_PROVISION}" == "true" ]]; then
  if [[ -z "${DB_PASSWORD:-}" ]]; then
    DB_PASSWORD="${DEFAULT_DB_PASSWORD}"
    echo "Using default non-production DB_PASSWORD for auto-provision mode."
  else
    echo "Using provided DB_PASSWORD from environment."
  fi
else
  : "${DB_HOST:?Set DB_HOST for existing-cluster mode (AUTO_PROVISION=false)}"
  : "${DB_PASSWORD:?Set DB_PASSWORD for existing-cluster mode (AUTO_PROVISION=false)}"
  echo "Using existing AlloyDB cluster mode (AUTO_PROVISION=false)."
fi

export PROJECT_ID
export REGION
export SERVICE_NAME
export AUTO_PROVISION
export SEED_LIMIT
export APP_NL_TO_SQL_TEMPLATE
export DB_PASSWORD
export DB_HOST

cd "${ROOT_DIR}"

echo "Starting one-click provisioning with:"
echo "  PROJECT_ID=${PROJECT_ID}"
echo "  REGION=${REGION}"
echo "  SERVICE_NAME=${SERVICE_NAME}"
echo "  AUTO_PROVISION=${AUTO_PROVISION}"
echo "  SEED_LIMIT=${SEED_LIMIT}"

bash scripts/bootstrap_track3.sh
