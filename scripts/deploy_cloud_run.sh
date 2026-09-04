#!/usr/bin/env bash

set -euo pipefail

PROJECT_ID="memresolve-ai-rohid35"
REGION="us-central1"
SERVICE_NAME="memresolve-ai"
SERVICE_ACCOUNT="memresolve-runtime@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud run deploy "${SERVICE_NAME}" \
  --source . \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --service-account "${SERVICE_ACCOUNT}" \
  --port 8080 \
  --cpu 1 \
  --memory 2Gi \
  --timeout 300 \
  --min-instances 0 \
  --max-instances 3 \
  --concurrency 20 \
  --no-allow-unauthenticated \
  --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=true" \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --set-env-vars "GOOGLE_CLOUD_LOCATION=${REGION}" \
  --set-env-vars "MEM_RESOLVE_MODEL=gemini-2.5-flash" \
  --set-env-vars "MEM_RESOLVE_ENVIRONMENT=gcp" \
  --set-env-vars "DATA_BACKEND=firestore" \
  --set-env-vars "KNOWLEDGE_BACKEND=chroma" \
  --set-env-vars "CHROMA_PERSIST_DIRECTORY=data/chroma" \
  --set-env-vars "CHROMA_COLLECTION=memresolve-policies" \
  --set-env-vars "MCP_TRANSPORT=stdio"