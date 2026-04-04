import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from elasticsearch import Elasticsearch

ELASTIC_CLOUD_URL = os.environ["ELASTIC_CLOUD_URL"]
ELASTIC_API_KEY   = os.environ["ELASTIC_API_KEY"]

INDEX_NAME = "hello"


def main() -> None:
    es = Elasticsearch(ELASTIC_CLOUD_URL, api_key=ELASTIC_API_KEY)

    # 1. 疎通確認
    print("=== 1. info ===")
    info = es.info()
    print(f"cluster_name: {info['cluster_name']}")
    print(f"version: {info['version']['number']}")

    # 2. インデックス作成 + ドキュメント投入
    print("\n=== 2. index document ===")
    resp = es.index(
        index=INDEX_NAME,
        document={"message": "hello world", "tag": "test"},
    )
    print(f"result: {resp['result']}")
    print(f"_id: {resp['_id']}")

    # 3. 検索
    print("\n=== 3. search ===")
    es.indices.refresh(index=INDEX_NAME)
    result = es.search(
        index=INDEX_NAME,
        query={"match": {"message": "hello"}},
    )
    print(f"total hits: {result['hits']['total']['value']}")
    for hit in result["hits"]["hits"]:
        print(f"  -> {hit['_source']}")

    # 4. クリーンアップ
    print("\n=== 4. cleanup ===")
    es.indices.delete(index=INDEX_NAME)
    print("index deleted")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
