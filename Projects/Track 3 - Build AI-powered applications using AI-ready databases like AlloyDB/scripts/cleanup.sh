#!/usr/bin/env bash
set -euo pipefail

: "${PROJECT_ID:?Set PROJECT_ID}"
: "${REGION:?Set REGION}"
: "${SERVICE_NAME:?Set SERVICE_NAME}"

FULL_CLEANUP="${FULL_CLEANUP:-false}"
DELETE_NETWORK_RESOURCES="${DELETE_NETWORK_RESOURCES:-false}"
NETWORK="${NETWORK:-default}"
ALLOC_RANGE_NAME="${ALLOC_RANGE_NAME:-google-managed-services-${NETWORK}}"
CLUSTER_ID="${CLUSTER_ID:-track3-alloydb-cluster}"
INSTANCE_ID="${INSTANCE_ID:-track3-alloydb-primary}"
VPC_CONNECTOR_NAME="${VPC_CONNECTOR_NAME:-track3-vpc-connector}"

gcloud config set project "${PROJECT_ID}" >/dev/null

gcloud run services delete "${SERVICE_NAME}" \
  --region "${REGION}" \
  --quiet

echo "Cloud Run service deleted."

if [[ "${FULL_CLEANUP}" == "true" ]]; then
  echo "Running full cleanup for AlloyDB resources..."

  gcloud alloydb instances delete "${INSTANCE_ID}" \
    --cluster "${CLUSTER_ID}" \
    --region "${REGION}" \
    --quiet >/dev/null 2>&1 || true

  gcloud alloydb clusters delete "${CLUSTER_ID}" \
    --region "${REGION}" \
    --quiet >/dev/null 2>&1 || true

  gcloud compute networks vpc-access connectors delete "${VPC_CONNECTOR_NAME}" \
    --region "${REGION}" \
    --quiet >/dev/null 2>&1 || true

  if [[ "${DELETE_NETWORK_RESOURCES}" == "true" ]]; then
    gcloud services vpc-peerings delete \
      --service=servicenetworking.googleapis.com \
      --network="${NETWORK}" >/dev/null 2>&1 || true

    gcloud compute addresses delete "${ALLOC_RANGE_NAME}" \
      --global \
      --quiet >/dev/null 2>&1 || true
  fi

  echo "Full cleanup completed."
else
  echo "Set FULL_CLEANUP=true to delete AlloyDB resources as well."
fi
