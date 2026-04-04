#!/usr/bin/env bash
# Artifact Registry の Terraform import（冪等）
# Usage: scripts/setup/tf_import_registry.sh <TF_DIR> <PROJECT_ID> <REGION> <REPO>
set -euo pipefail

TF_DIR="${1:?TF_DIR is required}"
PROJECT_ID="${2:?PROJECT_ID is required}"
REGION="${3:?REGION is required}"
REPO="${4:?REPO is required}"

cd "$TF_DIR"

# state に存在するか → import 不要
if terraform state show module.registry.google_artifact_registry_repository.repo > /dev/null 2>&1; then
  echo "Artifact Registry import 確認完了（state に存在）"
  exit 0
fi

# import 試行（既に存在しなくても失敗を許容）
terraform import -input=false \
  module.registry.google_artifact_registry_repository.repo \
  "projects/${PROJECT_ID}/locations/${REGION}/repositories/${REPO}" 2>/dev/null || true

echo "Artifact Registry import 確認完了"
