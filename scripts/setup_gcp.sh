#!/usr/bin/env bash

set -euo pipefail

PROJECT_ID="memresolve-ai-rohid35"
REGION="us-central1"
SERVICE_ACCOUNT_NAME="memresolve-runtime"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud config set project "${PROJECT_ID}"

gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com \
  firestore.googleapis.com \
  --project "${PROJECT_ID}"

if ! gcloud iam service-accounts describe \
  "${SERVICE_ACCOUNT_EMAIL}" \
  --project "${PROJECT_ID}" >/dev/null 2>&1
then
  gcloud iam service-accounts create \
    "${SERVICE_ACCOUNT_NAME}" \
    --project "${PROJECT_ID}" \
    --display-name "MemResolve AI Runtime"
fi

for role in \
  roles/aiplatform.user \
  roles/datastore.user \
  roles/logging.logWriter
do
  gcloud projects add-iam-policy-binding \
    "${PROJECT_ID}" \
    --member "serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role "${role}" \
    --condition=None
done

echo
echo "GCP setup completed."
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Runtime service account: ${SERVICE_ACCOUNT_EMAIL}"