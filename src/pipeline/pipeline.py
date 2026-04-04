"""RAG評価 Vertex AI Pipeline 定義"""

from kfp import dsl

from components.run_evaluation import run_evaluation


@dsl.pipeline(
    name="doc-qa-rag-evaluation",
    description="RAG検索・回答品質の定期評価パイプライン",
    pipeline_root="gs://mlops-dev-a-doc-qa/pipeline-artifacts",
)
def rag_evaluation_pipeline(
    project_id: str = "mlops-dev-a",
    region: str = "asia-northeast1",
    search_type: str = "hybrid",
    top_k: int = 10,
    google_ai_studio_api_key: str = "",
):
    """RAG評価を実行し、結果を GCS に保存する。"""
    bucket_name = "mlops-dev-a-doc-qa"
    gcs_upload = f"gs://{bucket_name}/eval-results"

    run_evaluation(
        search_type=search_type,
        top_k=top_k,
        gcs_upload=gcs_upload,
        gcp_project=project_id,
        gcp_region=region,
        google_ai_studio_api_key=google_ai_studio_api_key,
    )
