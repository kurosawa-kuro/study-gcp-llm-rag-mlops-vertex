"""Terraformオペレーション"""
import subprocess

from config import JOB_NAME, PROJECT_ID, REGION, REPO_NAME, SECRET_NAME, dispatch

TF_DIR = "terraform"

INFRA_TARGETS = [
    "-target=ec_deployment.hello",
    "-target=google_artifact_registry_repository.hello",
    "-target=google_secret_manager_secret.elastic_api_key",
    "-target=google_secret_manager_secret_version.elastic_api_key",
    "-target=google_secret_manager_secret_iam_member.hello",
]


def tf_run(args: list[str]) -> None:
    subprocess.run(["terraform"] + args, cwd=TF_DIR, check=True)


def init() -> None:
    tf_run(["init"])


def plan() -> None:
    tf_run(["plan"])


def apply() -> None:
    tf_run(["apply", "-auto-approve"])


def apply_infra() -> None:
    tf_run(["apply", "-auto-approve"] + INFRA_TARGETS)


def destroy() -> None:
    tf_run(["destroy", "-auto-approve"])


def import_resources() -> None:
    imports = [
        ("google_artifact_registry_repository.hello",
         f"projects/{PROJECT_ID}/locations/{REGION}/repositories/{REPO_NAME}"),
        ("google_secret_manager_secret.elastic_api_key",
         f"projects/{PROJECT_ID}/secrets/{SECRET_NAME}"),
        ("google_cloud_run_v2_job.hello",
         f"projects/{PROJECT_ID}/locations/{REGION}/jobs/{JOB_NAME}"),
    ]
    for addr, resource_id in imports:
        tf_run(["import", addr, resource_id])


if __name__ == "__main__":
    dispatch({
        "init": init,
        "plan": plan,
        "apply": apply,
        "apply-infra": apply_infra,
        "destroy": destroy,
        "import": import_resources,
    })
