"""共通設定・ユーティリティ（.envから読み取り）"""
import os
import subprocess
import sys

PROJECT_ID = os.environ["PROJECT_ID"]
REGION = os.environ["REGION"]
DEPLOYMENT_NAME = os.environ["DEPLOYMENT_NAME"]
JOB_NAME = os.environ["JOB_NAME"]
REPO_NAME = os.environ["REPO_NAME"]
SECRET_NAME = os.environ["SECRET_NAME"]
IMAGE_URI = f"{REGION}-docker.pkg.dev/{PROJECT_ID}/{REPO_NAME}/{JOB_NAME}:latest"


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, **kwargs)


def dispatch(actions: dict[str, callable]) -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action not in actions:
        print(f"Usage: {sys.argv[0]} [{'/'.join(actions)}]")
        sys.exit(1)
    actions[action]()
