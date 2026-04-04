"""RAG評価コンテナコンポーネント

カスタム Docker イメージ内で evaluate.py を実行する。
環境変数は entrypoint.sh 経由で設定する。
"""

from kfp import dsl


@dsl.container_component
def run_evaluation(
    search_type: str,
    top_k: int,
    gcs_upload: str,
    gcp_project: str,
    gcp_region: str,
    google_ai_studio_api_key: str,
):
    """RAG評価を実行し、結果を GCS にアップロードする。"""
    return dsl.ContainerSpec(
        image="asia-northeast1-docker.pkg.dev/mlops-dev-a/mlops-dev-a-docker/doc-qa-eval:latest",
        command=["bash", "/app/entrypoint.sh"],
        args=[
            gcp_project,
            gcp_region,
            google_ai_studio_api_key,
            "--search-type", search_type,
            "--top-k", top_k,
            "--save-as", "pipeline",
            "--gcs-upload", gcs_upload,
        ],
    )
