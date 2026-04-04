"""RAG評価スクリプト（メイン）

検索品質（Recall@K / MRR）と回答品質（Exact Match / ROUGE-L）を評価する。
検索モジュールを直接呼び出し、APIを経由しない。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# shared/ と API モジュールをインポートパスに追加
_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT / "shared"))
sys.path.insert(0, str(_ROOT / "src" / "doc-qa" / "api"))

import vertexai
from google.cloud import bigquery, secretmanager
from elasticsearch import Elasticsearch

from config import get, setup_logging
from search.embedder import embed_query
from search.retriever import search_bigquery_vector, search_elasticsearch, hybrid_search
from search.reranker import reciprocal_rank_fusion
from generation.generator import generate_answer
from metrics import recall_at_k, find_first_relevant_rank, mrr, exact_match, rouge_l

logger = setup_logging("eval")

# === 設定（main.py と同じパターン）===
GCP_PROJECT = os.environ.get("GCP_PROJECT", get("gcp.project_id", "mlops-dev-a"))
GCP_REGION = os.environ.get("GCP_REGION", get("gcp.region", "asia-northeast1"))
BQ_DATASET = os.environ.get("BQ_DATASET", get("bigquery.dataset", "doc_qa_dataset"))
BQ_TABLE = os.environ.get("BQ_TABLE", get("bigquery.table", "documents"))
ES_SECRET_NAME = os.environ.get("ES_SECRET_NAME", get("elasticsearch.secret_name", "elastic-cloud-api-key"))
ES_INDEX = os.environ.get("ES_INDEX", get("elasticsearch.index_name", "doc-qa"))
RRF_K = get("api.rrf_k", 60)

EVAL_DIR = Path(__file__).resolve().parent
RESULTS_DIR = EVAL_DIR / "results"
K_VALUES = [1, 3, 5, 10]


def _get_es_client() -> Elasticsearch:
    """Secret Manager から接続情報を取得して ES クライアントを返す。"""
    sm = secretmanager.SecretManagerServiceClient()
    name = f"projects/{GCP_PROJECT}/secrets/{ES_SECRET_NAME}/versions/latest"
    response = sm.access_secret_version(request={"name": name})
    secret = json.loads(response.payload.data.decode("utf-8"))
    return Elasticsearch(
        secret["cloud_url"],
        basic_auth=(secret["username"], secret["password"]),
    )


def _init_clients() -> tuple[bigquery.Client, Elasticsearch]:
    """GCP / ES クライアントを初期化する。"""
    vertexai.init(project=GCP_PROJECT, location=GCP_REGION)
    bq_client = bigquery.Client(project=GCP_PROJECT)
    es_client = _get_es_client()
    logger.info("クライアント初期化完了")
    return bq_client, es_client


def _search(
    bq_client: bigquery.Client,
    es_client: Elasticsearch,
    query_text: str,
    query_embedding: list[float],
    top_k: int,
    search_type: str,
) -> list[dict]:
    """検索タイプに応じた検索を実行する。"""
    if search_type == "vector":
        return search_bigquery_vector(bq_client, BQ_DATASET, BQ_TABLE, query_embedding, top_k)
    elif search_type == "elasticsearch":
        return search_elasticsearch(es_client, ES_INDEX, query_text, top_k)
    else:
        vector_results, fulltext_results = hybrid_search(
            bq_client, es_client, BQ_DATASET, BQ_TABLE, ES_INDEX,
            query_text, query_embedding, top_k,
        )
        return reciprocal_rank_fusion(vector_results, fulltext_results, top_k, k=RRF_K)


def _load_queries(path: Path) -> list[dict]:
    """JSONL ファイルから評価クエリを読み込む。"""
    queries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                queries.append(json.loads(line))
    return queries


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG評価スクリプト")
    parser.add_argument("--search-type", choices=["vector", "elasticsearch", "hybrid"],
                        default="hybrid", help="検索タイプ（デフォルト: hybrid）")
    parser.add_argument("--save-as", type=str, default=None,
                        help="結果ラベル（例: baseline）")
    parser.add_argument("--top-k", type=int, default=10,
                        help="検索結果の取得件数（デフォルト: 10）")
    parser.add_argument("--queries", type=str, default=str(EVAL_DIR / "queries_eval.jsonl"),
                        help="評価クエリファイルのパス")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="結果出力先ディレクトリ（デフォルト: scripts/eval/results/）")
    parser.add_argument("--gcs-upload", type=str, default=None,
                        help="結果アップロード先GCSパス（例: gs://bucket/eval-results/）")
    args = parser.parse_args()

    queries = _load_queries(Path(args.queries))
    logger.info(f"評価クエリ: {len(queries)} 件, 検索タイプ: {args.search_type}")

    bq_client, es_client = _init_clients()

    per_query_results = []
    all_ranks = []

    for q in queries:
        query_id = q["query_id"]
        query_text = q["query"]
        relevant_keywords = q["relevant_keywords"]
        expected_keywords = q["expected_answer_keywords"]

        logger.info(f"[{query_id}] {query_text}")

        query_embedding = embed_query(query_text)
        results = _search(bq_client, es_client, query_text, query_embedding, args.top_k, args.search_type)

        rank = find_first_relevant_rank(results, relevant_keywords)
        all_ranks.append(rank)

        recalls = {f"recall@{k}": recall_at_k(results, relevant_keywords, k) for k in K_VALUES}

        answer = generate_answer(query_text, results)
        em = exact_match(answer, expected_keywords)

        reference = " ".join(expected_keywords)
        rl = rouge_l(answer, reference)

        per_query_results.append({
            "query_id": query_id,
            "query": query_text,
            "rank": rank,
            **recalls,
            "exact_match": em,
            "rouge_l": round(rl, 4),
            "answer": answer,
        })

        logger.info(f"  rank={rank}, EM={em}, ROUGE-L={rl:.4f}")

    num_queries = len(queries)
    retrieval_metrics = {
        f"recall@{k}": round(sum(r[f"recall@{k}"] for r in per_query_results) / num_queries, 4)
        for k in K_VALUES
    }
    retrieval_metrics["mrr"] = round(mrr(all_ranks), 4)

    generation_metrics = {
        "exact_match": round(sum(1 for r in per_query_results if r["exact_match"]) / num_queries, 4),
        "rouge_l": round(sum(r["rouge_l"] for r in per_query_results) / num_queries, 4),
    }

    output = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "model": f"{get('ingestion.embedding_model', 'unknown')} + {get('api.gemini_model', 'unknown')}",
        "search_type": args.search_type,
        "top_k": args.top_k,
        "num_queries": num_queries,
        "retrieval": retrieval_metrics,
        "generation": generation_metrics,
        "per_query": per_query_results,
    }

    label = args.save_as or "eval"
    date_str = datetime.now().strftime("%Y%m%d")
    results_dir = Path(args.output_dir) if args.output_dir else RESULTS_DIR
    results_dir.mkdir(parents=True, exist_ok=True)
    output_path = results_dir / f"{label}_{date_str}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    logger.info(f"結果保存: {output_path}")

    if args.gcs_upload:
        _upload_to_gcs(output_path, args.gcs_upload)

    _print_summary(args.search_type, num_queries, retrieval_metrics, generation_metrics)


def _upload_to_gcs(local_path: Path, gcs_prefix: str) -> None:
    """結果ファイルを GCS にアップロードする。"""
    from google.cloud import storage as gcs_storage

    gcs_prefix = gcs_prefix.rstrip("/")
    bucket_name = gcs_prefix.replace("gs://", "").split("/")[0]
    blob_prefix = "/".join(gcs_prefix.replace("gs://", "").split("/")[1:])
    blob_path = f"{blob_prefix}/{local_path.name}" if blob_prefix else local_path.name

    client = gcs_storage.Client(project=GCP_PROJECT)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    blob.upload_from_filename(str(local_path))
    logger.info(f"GCS アップロード完了: gs://{bucket_name}/{blob_path}")


def _print_summary(
    search_type: str, num_queries: int,
    retrieval: dict, generation: dict,
) -> None:
    """評価結果のサマリーをコンソール出力する。"""
    print("\n=== RAG 評価結果 ===")
    print(f"検索タイプ: {search_type}")
    print(f"クエリ数:   {num_queries}")
    print()
    print("--- 検索品質 (Retrieval) ---")
    for k in K_VALUES:
        print(f"Recall@{k:<3}  {retrieval[f'recall@{k}']:.4f}")
    print(f"MRR:        {retrieval['mrr']:.4f}")
    print()
    print("--- 回答品質 (Generation) ---")
    print(f"Exact Match: {generation['exact_match']:.4f}")
    print(f"ROUGE-L:     {generation['rouge_l']:.4f}")
    print()


if __name__ == "__main__":
    main()
