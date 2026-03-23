#!/usr/bin/env bash
set -euo pipefail

: "${PROJECT_ID:?Set PROJECT_ID}"
: "${REGION:?Set REGION}"
: "${SERVICE_NAME:?Set SERVICE_NAME}"
: "${DB_HOST:?Set DB_HOST}"
: "${DB_PORT:=5432}"
: "${DB_NAME:=postgres}"
: "${DB_USER:?Set DB_USER}"
: "${DB_PASSWORD:?Set DB_PASSWORD}"
: "${APP_NL_TO_SQL_TEMPLATE:=}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

gcloud config set project "${PROJECT_ID}" >/dev/null

gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com >/dev/null

cd "${ROOT_DIR}"

if [[ -z "${APP_NL_TO_SQL_TEMPLATE}" ]]; then
  ENV_VARS="DB_HOST=${DB_HOST},DB_PORT=${DB_PORT},DB_NAME=${DB_NAME},DB_USER=${DB_USER},DB_PASSWORD=${DB_PASSWORD},DB_SSLMODE=require,APP_NL_TO_SQL_TEMPLATE="
else
  ENV_VARS="DB_HOST=${DB_HOST},DB_PORT=${DB_PORT},DB_NAME=${DB_NAME},DB_USER=${DB_USER},DB_PASSWORD=${DB_PASSWORD},DB_SSLMODE=require,APP_NL_TO_SQL_TEMPLATE=${APP_NL_TO_SQL_TEMPLATE}"
fi

DEPLOY_ARGS=(
  "${SERVICE_NAME}"
  --source .
  --region "${REGION}"
  --allow-unauthenticated
  --min-instances 0
  --max-instances 1
  --set-env-vars "${ENV_VARS}"
  --port 8080
)

if [[ -n "${VPC_CONNECTOR_NAME:-}" ]]; then
  DEPLOY_ARGS+=(--vpc-connector "${VPC_CONNECTOR_NAME}" --vpc-egress all-traffic)
fi

gcloud run deploy \
  "${DEPLOY_ARGS[@]}"

URL="$(gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --format='value(status.url)')"

echo "Cloud Run URL: ${URL}"
