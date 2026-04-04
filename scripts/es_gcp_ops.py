"""Elastic Cloud 接続確認用 GCP操作"""
import subprocess

from es_config import JOB_NAME, PROJECT_ID, REGION
from core import dispatch


def auth_docker() -> None:
    subprocess.run(["gcloud", "auth", "configure-docker", f"{REGION}-docker.pkg.dev"], check=True)


def execute() -> None:
    subprocess.run(["gcloud", "run", "jobs", "execute", JOB_NAME, f"--region={REGION}", "--wait"], check=True)


def logs() -> None:
    subprocess.run([
        "gcloud", "logging", "read",
        f"resource.type=cloud_run_job AND resource.labels.job_name={JOB_NAME}",
        "--limit=50",
        "--format=value(textPayload)",
        f"--project={PROJECT_ID}",
        "--order=asc",
    ], check=True)


if __name__ == "__main__":
    dispatch({
        "auth-docker": auth_docker,
        "execute": execute,
        "logs": logs,
    })
