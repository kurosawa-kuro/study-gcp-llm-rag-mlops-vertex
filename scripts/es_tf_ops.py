"""Elastic Cloud 関連 Terraform操作（統合済み terraform/ を参照）"""
import subprocess
from pathlib import Path

from es_config import PROJECT_ID, SECRET_NAME
from core import dispatch

TF_DIR = str(Path(__file__).resolve().parent.parent / "terraform")

INFRA_TARGETS = [
    "-target=ec_deployment.doc_qa",
    "-target=google_secret_manager_secret.elastic_api_key",
    "-target=google_secret_manager_secret_version.elastic_api_key",
    "-target=google_secret_manager_secret_iam_member.es_secret_access",
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
        ("google_secret_manager_secret.elastic_api_key",
         f"projects/{PROJECT_ID}/secrets/{SECRET_NAME}"),
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
