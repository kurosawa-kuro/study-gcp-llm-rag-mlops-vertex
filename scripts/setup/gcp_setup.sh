#!/usr/bin/env bash
# GCP 初回セットアップ（全て冪等）
# Usage: scripts/setup/gcp_setup.sh <PROJECT_ID> <REGION> <TF_SA> <COMPUTE_SA>
set -euo pipefail

PROJECT_ID="${1:?PROJECT_ID is required}"
REGION="${2:?REGION is required}"
TF_SA="${3:?TF_SA is required}"
COMPUTE_SA="${4:?COMPUTE_SA is required}"

# --- API 有効化 ---
echo "=== GCP API 有効化 ==="
gcloud services enable \
  artifactregistry.googleapis.com \
  run.googleapis.com \
  compute.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com \
  cloudscheduler.googleapis.com \
  bigquery.googleapis.com \
  aiplatform.googleapis.com \
  generativelanguage.googleapis.com \
  secretmanager.googleapis.com \
  --project="$PROJECT_ID"

# --- Terraform SA 権限 ---
echo "=== Terraform SA 権限設定 ==="
for ROLE in roles/editor roles/run.admin roles/resourcemanager.projectIamAdmin roles/secretmanager.admin; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$TF_SA" \
    --role="$ROLE" --quiet > /dev/null 2>&1
done
echo "Terraform SA 権限設定完了"

# --- Vertex AI 権限 ---
echo "=== Vertex AI 権限設定 ==="
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$COMPUTE_SA" \
  --role="roles/aiplatform.user" --quiet > /dev/null 2>&1
echo "Vertex AI 権限設定完了"

# --- Docker 認証 ---
echo "=== Docker 認証設定 ==="
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet 2>/dev/null
echo "Docker 認証設定完了"
