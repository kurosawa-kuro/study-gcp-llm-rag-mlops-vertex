#!/usr/bin/env python3
"""リセット: GCPリソース全削除 → ローカル状態クリーン"""

import json
import shutil
import subprocess

from core import PROJECT_ID, REGION, ROOT, run

TF_DIR = ROOT / "terraform"

CLEANUP_DIRS = [".terraform"]
CLEANUP_FILES = [".terraform.lock.hcl", "terraform.tfstate", "terraform.tfstate.backup"]

ML_DIR = ROOT / "src" / "batch"
ML_CLEANUP_DIRS = ["outputs", "mlruns", "mlartifacts"]
ML_CLEANUP_FILES = ["mlflow.db"]


def clean_terraform_local() -> None:
    print("\n==> Terraformローカル状態クリーン")
    for name in CLEANUP_DIRS:
        target = TF_DIR / name
        if target.is_dir():
            shutil.rmtree(target)
            print(f"  削除: {target}")

    for name in CLEANUP_FILES:
        target = TF_DIR / name
        if target.is_file():
            target.unlink()
            print(f"  削除: {target}")


def clean_ml_local() -> None:
    print("\n==> ML成果物クリーン")
    for name in ML_CLEANUP_DIRS:
        target = ML_DIR / name
        if target.is_dir():
            shutil.rmtree(target)
            print(f"  削除: {target}")

    for name in ML_CLEANUP_FILES:
        target = ML_DIR / name
        if target.is_file():
            target.unlink()
            print(f"  削除: {target}")


def clean_vertex_ai() -> None:
    """Vertex AI Endpoint / Model を冪等に削除する。"""
    print("\n==> Vertex AI クリーンアップ")

    # Endpoint 一覧を取得
    result = subprocess.run(
        ["gcloud", "ai", "endpoints", "list",
         f"--region={REGION}", f"--project={PROJECT_ID}",
         "--format=json"],
        capture_output=True, text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        print("  Vertex AI Endpoint なし（スキップ）")
        return

    endpoints = json.loads(result.stdout)
    if not endpoints:
        print("  Vertex AI Endpoint なし（スキップ）")
        return

    for ep in endpoints:
        ep_id = ep["name"].split("/")[-1]
        display_name = ep.get("displayName", "")
        print(f"  Endpoint 削除中: {display_name} ({ep_id})")

        # デプロイ済みモデルを全て undeploy
        for dm in ep.get("deployedModels", []):
            dm_id = dm["id"]
            print(f"    Undeploy: deployed_model_id={dm_id}")
            subprocess.run(
                ["gcloud", "ai", "endpoints", "undeploy-model", ep_id,
                 f"--region={REGION}", f"--project={PROJECT_ID}",
                 f"--deployed-model-id={dm_id}", "--quiet"],
                capture_output=True,
            )

        # Endpoint 削除
        subprocess.run(
            ["gcloud", "ai", "endpoints", "delete", ep_id,
             f"--region={REGION}", f"--project={PROJECT_ID}", "--quiet"],
            capture_output=True,
        )
        print(f"    Endpoint 削除完了: {ep_id}")

    # Model Registry のモデルを削除
    result = subprocess.run(
        ["gcloud", "ai", "models", "list",
         f"--region={REGION}", f"--project={PROJECT_ID}",
         "--format=json"],
        capture_output=True, text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        models = json.loads(result.stdout)
        for m in models:
            model_id = m["name"].split("/")[-1]
            display_name = m.get("displayName", "")
            print(f"  Model 削除中: {display_name} ({model_id})")
            subprocess.run(
                ["gcloud", "ai", "models", "delete", model_id,
                 f"--region={REGION}", f"--project={PROJECT_ID}", "--quiet"],
                capture_output=True,
            )


def clean_pipeline_artifacts() -> None:
    """Pipeline 関連のローカル成果物をクリーンする。"""
    print("\n==> Pipeline 成果物クリーン")
    pipeline_dir = ROOT / "src" / "pipeline"
    for name in ["pipeline.json", "__pycache__"]:
        target = pipeline_dir / name
        if target.is_dir():
            shutil.rmtree(target)
            print(f"  削除: {target}")
        elif target.is_file():
            target.unlink()
            print(f"  削除: {target}")
    # components/__pycache__
    pycache = pipeline_dir / "components" / "__pycache__"
    if pycache.is_dir():
        shutil.rmtree(pycache)
        print(f"  削除: {pycache}")


def main() -> None:
    clean_vertex_ai()
    run("make tf-destroy")
    clean_terraform_local()
    clean_ml_local()
    clean_pipeline_artifacts()

    run("docker images --format '{{.Repository}}:{{.Tag}}' "
        "| grep mlops-dev-a/mlops-dev-a-docker "
        "| xargs -r docker rmi", allow_fail=True)

    print("\n==> リセット完了。make deploy で再構築できます。")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "clean-vertex":
        clean_vertex_ai()
    else:
        main()
