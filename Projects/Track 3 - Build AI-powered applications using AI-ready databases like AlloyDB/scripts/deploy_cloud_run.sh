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
: "${VPC_EGRESS:=private-ranges-only}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

gcloud config set project "${PROJECT_ID}" >/dev/null

gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com >/dev/null

cd "${ROOT_DIR}"

# Use a custom delimiter so SQL templates with commas are passed safely.
ALL_ENV_VALUES="${DB_HOST}${DB_PORT}${DB_NAME}${DB_USER}${DB_PASSWORD}${APP_NL_TO_SQL_TEMPLATE}"
ENV_DELIM=""
for CANDIDATE in "@" "|" "#" "%" "~" ":" ";"; do
  if [[ "${ALL_ENV_VALUES}" != *"${CANDIDATE}"* ]]; then
    ENV_DELIM="${CANDIDATE}"
    break
  fi
done

if [[ -z "${ENV_DELIM}" ]]; then
  echo "Unable to choose a safe delimiter for --set-env-vars." >&2
  exit 1
fi

ENV_VARS="^${ENV_DELIM}^DB_HOST=${DB_HOST}${ENV_DELIM}DB_PORT=${DB_PORT}${ENV_DELIM}DB_NAME=${DB_NAME}${ENV_DELIM}DB_USER=${DB_USER}${ENV_DELIM}DB_PASSWORD=${DB_PASSWORD}${ENV_DELIM}DB_SSLMODE=require${ENV_DELIM}APP_NL_TO_SQL_TEMPLATE=${APP_NL_TO_SQL_TEMPLATE}"

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
  CONNECTOR_STATE="$(gcloud compute networks vpc-access connectors describe "${VPC_CONNECTOR_NAME}" --region "${REGION}" --format='value(state)' 2>/dev/null || true)"
  if [[ "${CONNECTOR_STATE}" != "READY" ]]; then
    echo "VPC connector '${VPC_CONNECTOR_NAME}' is not READY (state='${CONNECTOR_STATE:-missing}')." >&2
    echo "Fix connector state before deploying Cloud Run with VPC access." >&2
    exit 1
  fi

  DEPLOY_ARGS+=(--vpc-connector "${VPC_CONNECTOR_NAME}" --vpc-egress "${VPC_EGRESS}")
fi

gcloud run deploy \
  "${DEPLOY_ARGS[@]}"

URL="$(gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --format='value(status.url)')"

echo "Cloud Run URL: ${URL}"
