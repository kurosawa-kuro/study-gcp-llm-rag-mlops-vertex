"""Vertex AI Pipeline のコンパイルと実行を行うスクリプト。

使い方:
  # コンパイルのみ
  python run_pipeline.py compile

  # コンパイル + 実行
  python run_pipeline.py run

  # パラメータを指定して実行
  python run_pipeline.py run --search-type vector

  # 週次スケジュール作成
  python run_pipeline.py schedule
"""

from __future__ import annotations

import argparse
import os

from google.cloud import aiplatform
from kfp import compiler

from pipeline import rag_evaluation_pipeline

PROJECT_ID = "mlops-dev-a"
REGION = "asia-northeast1"
PIPELINE_ROOT = "gs://mlops-dev-a-doc-qa/pipeline-artifacts"
SERVICE_ACCOUNT = f"doc-qa-runner@{PROJECT_ID}.iam.gserviceaccount.com"


def compile_pipeline(output_path: str = "eval_pipeline.json") -> str:
    """パイプラインを JSON にコンパイルする。"""
    compiler.Compiler().compile(
        pipeline_func=rag_evaluation_pipeline,
        package_path=output_path,
    )
    print(f"Pipeline コンパイル完了: {output_path}")
    return output_path


def run_pipeline(
    template_path: str = "eval_pipeline.json",
    search_type: str = "hybrid",
    top_k: int = 10,
    sync: bool = True,
) -> aiplatform.PipelineJob:
    """パイプラインをコンパイルして Vertex AI で実行する。"""
    aiplatform.init(project=PROJECT_ID, location=REGION)

    parameter_values = {
        "project_id": PROJECT_ID,
        "region": REGION,
        "search_type": search_type,
        "top_k": top_k,
        "google_ai_studio_api_key": os.environ.get("GOOGLE_AI_STUDIO_API_KEY", ""),
    }

    job = aiplatform.PipelineJob(
        display_name="doc-qa-rag-eval",
        template_path=template_path,
        pipeline_root=PIPELINE_ROOT,
        parameter_values=parameter_values,
    )
    job.run(sync=sync, service_account=SERVICE_ACCOUNT)
    print(f"Pipeline 実行完了: {job.resource_name}")
    return job


def create_schedule(
    template_path: str = "eval_pipeline.json",
    cron: str = "0 22 * * 0",
) -> None:
    """パイプラインの週次スケジュールを作成する。"""
    aiplatform.init(project=PROJECT_ID, location=REGION)

    parameter_values = {
        "project_id": PROJECT_ID,
        "region": REGION,
        "search_type": "hybrid",
        "top_k": 10,
        "google_ai_studio_api_key": os.environ.get("GOOGLE_AI_STUDIO_API_KEY", ""),
    }

    job = aiplatform.PipelineJob(
        display_name="doc-qa-rag-eval-scheduled",
        template_path=template_path,
        pipeline_root=PIPELINE_ROOT,
        parameter_values=parameter_values,
    )
    schedule = job.create_schedule(
        display_name="doc-qa-rag-eval-weekly",
        cron=cron,
        service_account=SERVICE_ACCOUNT,
    )
    print(f"スケジュール作成完了: {schedule.resource_name}")


def main():
    parser = argparse.ArgumentParser(description="RAG評価 Vertex AI Pipeline 実行ツール")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # compile
    compile_parser = subparsers.add_parser("compile", help="Pipeline をコンパイル")
    compile_parser.add_argument("--output", default="eval_pipeline.json")

    # run
    run_parser = subparsers.add_parser("run", help="Pipeline をコンパイルして実行")
    run_parser.add_argument("--search-type", default="hybrid",
                            choices=["vector", "elasticsearch", "hybrid"])
    run_parser.add_argument("--top-k", type=int, default=10)
    run_parser.add_argument("--async", dest="run_async", action="store_true")

    # schedule
    schedule_parser = subparsers.add_parser("schedule", help="週次スケジュールを作成")
    schedule_parser.add_argument("--cron", default="0 22 * * 0",
                                help="cron式（デフォルト: 毎週日曜22:00）")

    args = parser.parse_args()

    if args.command == "compile":
        compile_pipeline(args.output)
    elif args.command == "run":
        template_path = compile_pipeline()
        run_pipeline(
            template_path=template_path,
            search_type=args.search_type,
            top_k=args.top_k,
            sync=not args.run_async,
        )
    elif args.command == "schedule":
        template_path = compile_pipeline()
        create_schedule(template_path=template_path, cron=args.cron)


if __name__ == "__main__":
    main()
