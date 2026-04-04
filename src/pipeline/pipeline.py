from kfp import dsl

from components.compare_champion import compare_champion
from components.deploy_model import deploy_model
from components.evaluate_model import evaluate_model
from components.load_data import load_data
from components.quality_gate import quality_gate
from components.train_model import train_model


@dsl.pipeline(
    name="california-housing-pipeline",
    description="California Housing モデルの学習・評価・品質ゲート・Champion比較・デプロイ",
    pipeline_root="gs://mlops-dev-a-data/pipeline-artifacts",
)
def california_housing_pipeline(
    project_id: str = "mlops-dev-a",
    region: str = "asia-northeast1",
    bucket_name: str = "mlops-dev-a-data",
    test_size: float = 0.2,
    random_state: int = 42,
    n_estimators: int = 100,
    max_depth: int = 10,
    rmse_threshold: float = 0.8,
    improvement_threshold: float = 0.01,
    endpoint_display_name: str = "california-housing-endpoint",
    discord_webhook_url: str = "",
):
    # Step1: データ取得・分割
    load_task = load_data(
        test_size=test_size,
        random_state=random_state,
    )

    # Step2: モデル学習
    train_task = train_model(
        X_train_in=load_task.outputs["X_train_out"],
        y_train_in=load_task.outputs["y_train_out"],
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
    )

    # Step3: 評価・GCS保存・BigQuery記録
    eval_task = evaluate_model(
        model_in=train_task.outputs["model_out"],
        X_test_in=load_task.outputs["X_test_out"],
        y_test_in=load_task.outputs["y_test_out"],
        project_id=project_id,
        bucket_name=bucket_name,
        n_estimators=n_estimators,
        max_depth=max_depth,
    )

    # Step4: 品質ゲート
    gate_task = quality_gate(
        rmse=eval_task.outputs["rmse"],
        rmse_threshold=rmse_threshold,
        model_gcs_path=eval_task.outputs["model_gcs_path"],
        discord_webhook_url=discord_webhook_url,
    )

    # Step5: Champion/Challenger 比較（品質ゲート合格時のみ）
    with dsl.Condition(gate_task.outputs["is_passed"] == "true"):
        compare_task = compare_champion(
            challenger_rmse=eval_task.outputs["rmse"],
            challenger_model_path=eval_task.outputs["model_gcs_path"],
            improvement_threshold=improvement_threshold,
            project_id=project_id,
            discord_webhook_url=discord_webhook_url,
        )

        # Step6: デプロイ（Challenger が優位な場合のみ）
        with dsl.Condition(compare_task.outputs["should_deploy"] == "true"):
            deploy_model(
                model_gcs_path=eval_task.outputs["model_gcs_path"],
                project_id=project_id,
                region=region,
                endpoint_display_name=endpoint_display_name,
                run_id=eval_task.outputs["run_id"],
                rmse=eval_task.outputs["rmse"],
                mae=eval_task.outputs["mae"],
                discord_webhook_url=discord_webhook_url,
            )
