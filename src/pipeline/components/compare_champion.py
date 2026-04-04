from typing import NamedTuple

from kfp import dsl


@dsl.component(
    base_image="python:3.11-slim",
    packages_to_install=["google-cloud-bigquery==3.14.1"],
)
def compare_champion(
    challenger_rmse: float,
    challenger_model_path: str,
    improvement_threshold: float,
    project_id: str,
    discord_webhook_url: str,
) -> NamedTuple("Outputs", [("should_deploy", str), ("champion_rmse", float)]):
    """BigQuery から Champion モデルの RMSE を取得し、Challenger と比較する。"""
    import json
    import urllib.request
    from collections import namedtuple

    from google.cloud import bigquery

    def notify_discord(message: str, fields: list, color: int = 16776960):
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

    # BigQuery から現 Champion のメトリクスを取得
    # NOTE: challenger 自身のメトリクスは直前の evaluate_model で挿入済みなので除外する
    bq_client = bigquery.Client(project=project_id)
    query = f"""
    SELECT model_path, rmse
    FROM `{project_id}.mlops.metrics`
    WHERE model_path != @challenger_path
    ORDER BY rmse ASC
    LIMIT 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("challenger_path", "STRING", challenger_model_path),
        ]
    )
    rows = list(bq_client.query(query, job_config=job_config).result())

    Outputs = namedtuple("Outputs", ["should_deploy", "champion_rmse"])

    # 初回実行（Champion なし）
    if not rows:
        print("Champion なし（初回実行）: デプロイ実行")
        return Outputs(should_deploy="true", champion_rmse=999.0)

    champion_rmse = float(rows[0].rmse)
    champion_path = rows[0].model_path
    threshold = champion_rmse * (1.0 - improvement_threshold)

    print(f"Champion RMSE: {champion_rmse:.4f} (path: {champion_path})")
    print(f"Challenger RMSE: {challenger_rmse:.4f}")
    print(f"改善閾値: {threshold:.4f} (Champion * {1.0 - improvement_threshold})")

    if challenger_rmse < threshold:
        improvement_pct = (champion_rmse - challenger_rmse) / champion_rmse * 100
        print(f"Challenger が優位: {improvement_pct:.2f}% 改善 → デプロイ実行")
        return Outputs(should_deploy="true", champion_rmse=champion_rmse)
    else:
        print("有意な改善なし → デプロイスキップ")
        notify_discord(
            "Champion/Challenger 比較: 改善なし",
            [
                {"name": "Champion RMSE", "value": f"{champion_rmse:.4f}", "inline": True},
                {"name": "Challenger RMSE", "value": f"{challenger_rmse:.4f}", "inline": True},
                {"name": "改善閾値", "value": f"{improvement_threshold*100:.1f}%", "inline": True},
            ],
        )
        return Outputs(should_deploy="false", champion_rmse=champion_rmse)
