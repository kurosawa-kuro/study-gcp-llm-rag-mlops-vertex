from typing import NamedTuple

from kfp import dsl


@dsl.component(
    base_image="python:3.11-slim",
    packages_to_install=[
        "google-cloud-aiplatform==1.38.1",
        "google-cloud-storage==2.14.0",
    ],
)
def deploy_model(
    model_gcs_path: str,
    project_id: str,
    region: str,
    endpoint_display_name: str,
    run_id: str,
    rmse: float,
    mae: float,
    discord_webhook_url: str,
) -> NamedTuple("Outputs", [("endpoint_resource_name", str)]):
    """Vertex AI Endpoint にモデルをデプロイする。"""
    import json
    import re
    import urllib.request
    from collections import namedtuple

    from google.cloud import aiplatform, storage

    def notify_discord(message: str, fields: list, color: int = 3066993):
        if not discord_webhook_url:
            return
        payload = {
            "embeds": [{
                "title": message,
                "color": color,
                "fields": fields,
            }]
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            discord_webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req)

    aiplatform.init(project=project_id, location=region)

    # GCS からモデルを serving 用ディレクトリにコピー
    # sklearn serving container は artifact_uri 直下の model.pkl を期待する
    m = re.match(r"gs://([^/]+)/(.+)", model_gcs_path)
    src_bucket_name, src_blob_path = m.group(1), m.group(2)

    serving_dir = f"serving/{run_id}"
    serving_blob_path = f"{serving_dir}/model.pkl"
    serving_uri = f"gs://{src_bucket_name}/{serving_dir}"

    gcs_client = storage.Client(project=project_id)
    bucket = gcs_client.bucket(src_bucket_name)
    src_blob = bucket.blob(src_blob_path)
    bucket.copy_blob(src_blob, bucket, serving_blob_path)
    print(f"モデルコピー完了: {model_gcs_path} → gs://{src_bucket_name}/{serving_blob_path}")

    # Vertex AI Model Registry に登録
    model = aiplatform.Model.upload(
        display_name=f"california-housing-rf-{run_id[:8]}",
        artifact_uri=serving_uri,
        serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-3:latest",
    )
    print(f"Model Registry 登録完了: {model.resource_name}")

    # 既存 Endpoint を検索、なければ新規作成
    endpoints = aiplatform.Endpoint.list(
        filter=f'display_name="{endpoint_display_name}"',
    )
    if endpoints:
        endpoint = endpoints[0]
        print(f"既存 Endpoint 使用: {endpoint.resource_name}")
    else:
        endpoint = aiplatform.Endpoint.create(
            display_name=endpoint_display_name,
        )
        print(f"Endpoint 新規作成: {endpoint.resource_name}")

    # デプロイ（traffic 100%）
    model.deploy(
        endpoint=endpoint,
        machine_type="n1-standard-2",
        min_replica_count=1,
        max_replica_count=1,
        traffic_percentage=100,
    )
    print(f"デプロイ完了: {endpoint.resource_name}")

    # Discord 通知
    notify_discord(
        "モデルデプロイ成功",
        [
            {"name": "RMSE", "value": f"{rmse:.4f}", "inline": True},
            {"name": "MAE", "value": f"{mae:.4f}", "inline": True},
            {"name": "Endpoint", "value": endpoint.resource_name, "inline": False},
            {"name": "モデル", "value": model_gcs_path, "inline": False},
        ],
    )

    Outputs = namedtuple("Outputs", ["endpoint_resource_name"])
    return Outputs(endpoint_resource_name=endpoint.resource_name)
