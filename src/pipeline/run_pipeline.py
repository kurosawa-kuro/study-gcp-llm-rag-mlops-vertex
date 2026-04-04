"""Vertex AI Pipeline のコンパイルと実行を行うスクリプト。

使い方:
  # コンパイルのみ
  python run_pipeline.py compile

  # コンパイル + 実行
  python run_pipeline.py run

  # パラメータを指定して実行
  python run_pipeline.py run --rmse-threshold 0.6 --n-estimators 200
"""

import argparse

from google.cloud import aiplatform
from kfp import compiler

from pipeline import california_housing_pipeline

PROJECT_ID = "mlops-dev-a"
REGION = "asia-northeast1"
PIPELINE_ROOT = "gs://mlops-dev-a-data/pipeline-artifacts"


def compile_pipeline(output_path: str = "pipeline.json") -> str:
    compiler.Compiler().compile(
        pipeline_func=california_housing_pipeline,
        package_path=output_path,
    )
    print(f"Pipeline コンパイル完了: {output_path}")
    return output_path


def run_pipeline(
    template_path: str = "pipeline.json",
    rmse_threshold: float = 0.8,
    improvement_threshold: float = 0.01,
    n_estimators: int = 100,
    max_depth: int = 10,
    discord_webhook_url: str = "",
    sync: bool = True,
):
    aiplatform.init(project=PROJECT_ID, location=REGION)

    parameter_values = {
        "project_id": PROJECT_ID,
        "region": REGION,
        "bucket_name": "mlops-dev-a-data",
        "test_size": 0.2,
        "random_state": 42,
        "n_estimators": n_estimators,
        "max_depth": max_depth,
        "rmse_threshold": rmse_threshold,
        "improvement_threshold": improvement_threshold,
        "endpoint_display_name": "california-housing-endpoint",
        "discord_webhook_url": discord_webhook_url,
    }

    job = aiplatform.PipelineJob(
        display_name="california-housing-run",
        template_path=template_path,
        pipeline_root=PIPELINE_ROOT,
        parameter_values=parameter_values,
    )
    job.run(sync=sync)
    print(f"Pipeline 実行完了: {job.resource_name}")
    return job


def main():
    parser = argparse.ArgumentParser(description="Vertex AI Pipeline 実行ツール")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # compile コマンド
    compile_parser = subparsers.add_parser("compile", help="Pipeline をコンパイル")
    compile_parser.add_argument("--output", default="pipeline.json")

    # run コマンド
    run_parser = subparsers.add_parser("run", help="Pipeline をコンパイルして実行")
    run_parser.add_argument("--rmse-threshold", type=float, default=0.8)
    run_parser.add_argument("--improvement-threshold", type=float, default=0.01)
    run_parser.add_argument("--n-estimators", type=int, default=100)
    run_parser.add_argument("--max-depth", type=int, default=10)
    run_parser.add_argument("--discord-webhook-url", default="")
    run_parser.add_argument("--async", dest="run_async", action="store_true")

    args = parser.parse_args()

    if args.command == "compile":
        compile_pipeline(args.output)
    elif args.command == "run":
        template_path = compile_pipeline()
        run_pipeline(
            template_path=template_path,
            rmse_threshold=args.rmse_threshold,
            improvement_threshold=args.improvement_threshold,
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
            discord_webhook_url=args.discord_webhook_url,
            sync=not args.run_async,
        )


if __name__ == "__main__":
    main()
