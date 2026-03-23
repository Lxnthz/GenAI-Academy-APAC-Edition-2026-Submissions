#!/usr/bin/env bash
set -euo pipefail

: "${PROJECT_ID:?Set PROJECT_ID}"
: "${REGION:?Set REGION}"
: "${DB_PASSWORD:?Set DB_PASSWORD}"

NETWORK="${NETWORK:-default}"
ALLOC_RANGE_PREFIX="${ALLOC_RANGE_PREFIX:-16}"
ALLOC_RANGE_NAME="${ALLOC_RANGE_NAME:-google-managed-services-${NETWORK}}"
CLUSTER_ID="${CLUSTER_ID:-track3-alloydb-cluster}"
INSTANCE_ID="${INSTANCE_ID:-track3-alloydb-primary}"
VPC_CONNECTOR_NAME="${VPC_CONNECTOR_NAME:-track3-vpc-connector}"
DB_NAME="${DB_NAME:-postgres}"
DB_USER="${DB_USER:-postgres}"
CPU_COUNT="${CPU_COUNT:-2}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GENERATED_ENV_FILE="${ROOT_DIR}/.generated_env.sh"

gcloud config set project "${PROJECT_ID}" >/dev/null

gcloud services enable \
  alloydb.googleapis.com \
  compute.googleapis.com \
  servicenetworking.googleapis.com \
  vpcaccess.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com >/dev/null

if ! gcloud compute addresses describe "${ALLOC_RANGE_NAME}" --global >/dev/null 2>&1; then
  gcloud compute addresses create "${ALLOC_RANGE_NAME}" \
    --global \
    --purpose=VPC_PEERING \
    --addresses="10.10.0.0" \
    --prefix-length="${ALLOC_RANGE_PREFIX}" \
    --network="${NETWORK}" >/dev/null
fi

gcloud services vpc-peerings connect \
  --service=servicenetworking.googleapis.com \
  --network="${NETWORK}" \
  --ranges="${ALLOC_RANGE_NAME}" >/dev/null 2>&1 || true

if ! gcloud alloydb clusters describe "${CLUSTER_ID}" --region "${REGION}" >/dev/null 2>&1; then
  gcloud alloydb clusters create "${CLUSTER_ID}" \
    --region "${REGION}" \
    --network "projects/${PROJECT_ID}/global/networks/${NETWORK}" \
    --password "${DB_PASSWORD}" >/dev/null
fi

if ! gcloud alloydb instances describe "${INSTANCE_ID}" --cluster "${CLUSTER_ID}" --region "${REGION}" >/dev/null 2>&1; then
  gcloud alloydb instances create "${INSTANCE_ID}" \
    --cluster "${CLUSTER_ID}" \
    --region "${REGION}" \
    --instance-type PRIMARY \
    --cpu-count "${CPU_COUNT}" >/dev/null
fi

if ! gcloud compute networks vpc-access connectors describe "${VPC_CONNECTOR_NAME}" --region "${REGION}" >/dev/null 2>&1; then
  gcloud compute networks vpc-access connectors create "${VPC_CONNECTOR_NAME}" \
    --region "${REGION}" \
    --network "${NETWORK}" \
    --range "10.8.0.0/28" >/dev/null
fi

DB_HOST="$(gcloud alloydb instances describe "${INSTANCE_ID}" --cluster "${CLUSTER_ID}" --region "${REGION}" --format='value(ipAddress)')"
if [[ -z "${DB_HOST}" ]]; then
  DB_HOST="$(gcloud alloydb instances describe "${INSTANCE_ID}" --cluster "${CLUSTER_ID}" --region "${REGION}" --format='value(networkConfig.ipAddress)')"
fi

if [[ -z "${DB_HOST}" ]]; then
  echo "Failed to determine AlloyDB IP address automatically." >&2
  exit 1
fi

cat > "${GENERATED_ENV_FILE}" <<EOF
export PROJECT_ID="${PROJECT_ID}"
export REGION="${REGION}"
export DB_HOST="${DB_HOST}"
export DB_PORT="5432"
export DB_NAME="${DB_NAME}"
export DB_USER="${DB_USER}"
export DB_PASSWORD="${DB_PASSWORD}"
export NETWORK="${NETWORK}"
export CLUSTER_ID="${CLUSTER_ID}"
export INSTANCE_ID="${INSTANCE_ID}"
export VPC_CONNECTOR_NAME="${VPC_CONNECTOR_NAME}"
EOF

echo "Provisioning completed."
echo "Generated env file: ${GENERATED_ENV_FILE}"
echo "Detected DB_HOST: ${DB_HOST}"
