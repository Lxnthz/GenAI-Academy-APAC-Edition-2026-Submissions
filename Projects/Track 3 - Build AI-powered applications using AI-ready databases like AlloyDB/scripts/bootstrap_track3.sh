#!/usr/bin/env bash
set -euo pipefail

: "${PROJECT_ID:?Set PROJECT_ID}"
: "${REGION:?Set REGION}"
: "${SERVICE_NAME:?Set SERVICE_NAME}"

AUTO_PROVISION="${AUTO_PROVISION:-false}"

if [[ "${AUTO_PROVISION}" == "true" ]]; then
  : "${DB_PASSWORD:?Set DB_PASSWORD for auto provisioning}"
else
  : "${DB_HOST:?Set DB_HOST}"
  : "${DB_PASSWORD:?Set DB_PASSWORD}"
fi

: "${DB_PORT:=5432}"
: "${DB_NAME:=postgres}"
: "${DB_USER:=postgres}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SOURCE_DATASET="${SOURCE_DATASET:-${ROOT_DIR}/data/it_support_ticket_sample.csv}"
CLEANED_DATASET="${CLEANED_DATASET:-${ROOT_DIR}/data/it_support_ticket_en.csv}"
SEED_LIMIT="${SEED_LIMIT:-10000}"
RUN_FILTER="${RUN_FILTER:-true}"
: "${APP_NL_TO_SQL_TEMPLATE:=}"

export PROJECT_ID REGION SERVICE_NAME DB_HOST DB_PORT DB_NAME DB_USER DB_PASSWORD
export DATASET_PATH="${CLEANED_DATASET}"
export SEED_LIMIT
export APP_NL_TO_SQL_TEMPLATE

cd "${ROOT_DIR}"

if [[ "${AUTO_PROVISION}" == "true" ]]; then
  echo "[0/5] Auto provisioning AlloyDB and network resources"
  bash scripts/provision_alloydb.sh
  source "${ROOT_DIR}/.generated_env.sh"
  export PROJECT_ID REGION DB_HOST DB_PORT DB_NAME DB_USER DB_PASSWORD VPC_CONNECTOR_NAME NETWORK CLUSTER_ID INSTANCE_ID
fi

echo "[1/4] Preparing dataset"
if [[ "${RUN_FILTER}" == "true" ]]; then
  python3 scripts/filter_english_dataset.py --source "${SOURCE_DATASET}" --target "${CLEANED_DATASET}"
else
  echo "Skipping filter step (RUN_FILTER=${RUN_FILTER})"
fi

echo "[2/4] Applying DB schema and NL config"
bash scripts/setup_db.sh

echo "[3/4] Seeding data"
python3 scripts/seed_from_csv.py

echo "[4/4] Deploying Cloud Run service"
bash scripts/deploy_cloud_run.sh

echo "Completed."
