"""Elastic Cloud 接続確認用の共通設定（application.yml + .env から読み取り）"""
import os
from pathlib import Path

import yaml

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "env" / "config" / "application.yml"


def _load() -> dict:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


_CFG = _load()

PROJECT_ID = os.environ.get("PROJECT_ID", _CFG.get("gcp", {}).get("project_id", "mlops-dev-a"))
REGION = os.environ.get("REGION", _CFG.get("gcp", {}).get("region", "asia-northeast1"))
DEPLOYMENT_NAME = os.environ.get("DEPLOYMENT_NAME", _CFG.get("elasticsearch", {}).get("deployment_name", "doc-qa-es"))
JOB_NAME = os.environ.get("JOB_NAME", "hello-elastic-job")
REPO_NAME = os.environ.get("REPO_NAME", _CFG.get("registry", {}).get("repo_name", "mlops-dev-a-docker"))
SECRET_NAME = os.environ.get("SECRET_NAME", _CFG.get("elasticsearch", {}).get("secret_name", "elastic-cloud-api-key"))
IMAGE_URI = f"{REGION}-docker.pkg.dev/{PROJECT_ID}/{REPO_NAME}/{JOB_NAME}:latest"
