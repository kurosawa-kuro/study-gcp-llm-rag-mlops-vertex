"""GCP操作（Terraform管理外のオペレーション）"""
from config import JOB_NAME, PROJECT_ID, REGION, dispatch, run


def auth_docker() -> None:
    run(["gcloud", "auth", "configure-docker", f"{REGION}-docker.pkg.dev"])


def execute() -> None:
    run(["gcloud", "run", "jobs", "execute", JOB_NAME, f"--region={REGION}", "--wait"])


def logs() -> None:
    run([
        "gcloud", "logging", "read",
        f"resource.type=cloud_run_job AND resource.labels.job_name={JOB_NAME}",
        "--limit=50",
        "--format=value(textPayload)",
        f"--project={PROJECT_ID}",
        "--order=asc",
    ])


if __name__ == "__main__":
    dispatch({
        "auth-docker": auth_docker,
        "execute": execute,
        "logs": logs,
    })
