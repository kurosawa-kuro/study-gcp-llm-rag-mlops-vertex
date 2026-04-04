from typing import NamedTuple

from kfp import dsl


@dsl.component(
    base_image="python:3.11-slim",
    packages_to_install=[
        "scikit-learn==1.3.2",
        "pandas==2.1.4",
        "pyarrow==14.0.2",
        "google-cloud-storage==2.14.0",
        "google-cloud-bigquery==3.14.1",
    ],
)
def evaluate_model(
    model_in: dsl.Input[dsl.Model],
    X_test_in: dsl.Input[dsl.Dataset],
    y_test_in: dsl.Input[dsl.Dataset],
    project_id: str,
    bucket_name: str,
    n_estimators: int,
    max_depth: int,
    metrics_out: dsl.Output[dsl.Metrics],
) -> NamedTuple("Outputs", [("rmse", float), ("mae", float), ("model_gcs_path", str), ("run_id", str)]):
    """モデルを評価し、GCS に保存、BigQuery にメトリクスを記録する。"""
    import io
    import pickle
    import uuid
    from collections import namedtuple
    from datetime import datetime, timezone

    import numpy as np
    import pandas as pd
    from google.cloud import bigquery, storage
    from sklearn.metrics import mean_absolute_error, mean_squared_error

    # モデルとテストデータの読み込み
    with open(model_in.path, "rb") as f:
        model = pickle.load(f)

    X_test = pd.read_parquet(X_test_in.path)
    y_test = pd.read_parquet(y_test_in.path)["target"]

    # 評価
    y_pred = model.predict(X_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae = float(mean_absolute_error(y_test, y_pred))
    print(f"評価完了: RMSE={rmse:.4f}, MAE={mae:.4f}")

    # Vertex AI Metrics に記録
    metrics_out.log_metric("rmse", rmse)
    metrics_out.log_metric("mae", mae)
    metrics_out.log_metric("n_estimators", n_estimators)
    metrics_out.log_metric("max_depth", max_depth)

    # GCS にモデル保存（既存の batch/model_store.py と同じパス規約）
    now = datetime.now(timezone.utc)
    blob_path = f"models/{now.strftime('%Y%m%d')}/model_{now.strftime('%Y%m%d_%H%M%S')}.pkl"

    buf = io.BytesIO()
    pickle.dump(model, buf)
    buf.seek(0)

    gcs_client = storage.Client(project=project_id)
    bucket = gcs_client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    blob.upload_from_file(buf, content_type="application/octet-stream")

    model_gcs_path = f"gs://{bucket_name}/{blob_path}"
    print(f"モデル保存完了: {model_gcs_path}")

    # BigQuery にメトリクス記録
    run_id = str(uuid.uuid4())
    bq_client = bigquery.Client(project=project_id)
    table_id = f"{project_id}.mlops.metrics"
    row = {
        "run_id": run_id,
        "timestamp": now.isoformat(),
        "rmse": rmse,
        "mae": mae,
        "model_path": model_gcs_path,
        "n_estimators": n_estimators,
        "max_depth": max_depth,
    }
    errors = bq_client.insert_rows_json(table_id, [row])
    if errors:
        print(f"BigQuery insert エラー: {errors}")
    else:
        print(f"BigQuery メトリクス記録完了: run_id={run_id}")

    Outputs = namedtuple("Outputs", ["rmse", "mae", "model_gcs_path", "run_id"])
    return Outputs(rmse=rmse, mae=mae, model_gcs_path=model_gcs_path, run_id=run_id)
