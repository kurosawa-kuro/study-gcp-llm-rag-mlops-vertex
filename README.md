
# 社内ドキュメント検索・QAシステム

GCSにドキュメントをアップロードするだけでAIが根拠ドキュメント付きで日本語回答するQAシステム。

---

## アーキテクチャ

```
[GCS] → [Cloud Run Job: Ingestion] → [BigQuery + Elasticsearch]
                                              ↓
[ユーザー] → [Cloud Run Service: QA API] → [ハイブリッド検索 → Gemini回答]
```

- **Ingestion**: PDF/Word/TXT → チャンク分割 → Vertex AI Embedding → BigQuery(Vector) + Elasticsearch(kuromoji)
- **QA API**: クエリ → ハイブリッド検索 → RRFリランク → Gemini回答生成

---

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| LLM/RAG | Vertex AI Embedding API, Vertex AI Gemini |
| 検索 | BigQuery Vector Search + Elasticsearch (kuromoji) |
| API | FastAPI (Cloud Run Service) |
| バッチ | Cloud Run Job |
| IaC | Terraform (GCP + Elastic Cloud) |
| CI/CD | GitHub Actions |

---

## ディレクトリ構成

```
├── src/doc-qa/
│   ├── ingestion/    # ドキュメント取込パイプライン
│   └── api/          # QA API
├── src/elastic-search/  # Elastic Cloud基盤
├── terraform/        # GCPインフラ定義
├── scripts/          # ユーティリティ・監視
├── data/sample/      # サンプル社内規定
└── docs/             # 仕様・設計書
```

---

## 使い方

### 初回セットアップ

```bash
./scripts/setup_gcp.sh
./scripts/setup_terraform.sh
gcloud init
make gcp-setup
make tf-apply
```

### ドキュメント取込

```bash
# サンプルドキュメントをGCSにアップロード
./scripts/upload_doc.sh data/sample/

# Ingestion実行
make ingestion-run
```

### QAクエリ

```bash
# APIにクエリ送信
./scripts/query.sh "有給休暇の申請手続きを教えてください"
```

### ローカル開発

```bash
make test              # 全テスト実行
make ingestion-test    # Ingestionテスト
make qa-api-test       # QA APIテスト
```

### デプロイ

```bash
make deploy            # 全体デプロイ（Ingestion + QA API）
```

### 監視

```bash
make qa-api-monitor    # API健全性チェック + Discord通知
```

### コマンド一覧

```bash
make help
```
