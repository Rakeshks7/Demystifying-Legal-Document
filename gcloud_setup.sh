#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-your-project-id}"
REGION="${REGION:-asia-south1}"
UPLOAD_BUCKET="civilex-uploads-$PROJECT_ID"
RESULTS_BUCKET="civilex-results-$PROJECT_ID"

gcloud config set project "$PROJECT_ID"

gcloud services enable   aiplatform.googleapis.com   documentai.googleapis.com   run.googleapis.com   firestore.googleapis.com   cloudbuild.googleapis.com   secretmanager.googleapis.com

gcloud firestore databases create --location="$REGION" || true

gsutil mb -l "$REGION" "gs://$UPLOAD_BUCKET" || true
gsutil mb -l "$REGION" "gs://$RESULTS_BUCKET" || true

echo "Buckets created:"
echo "gs://$UPLOAD_BUCKET"
echo "gs://$RESULTS_BUCKET"