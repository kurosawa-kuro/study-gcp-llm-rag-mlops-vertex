
# 社内ドキュメント検索・QAシステム

GCSにドキュメントをアップロードするだけでAIが根拠ドキュメント付きで日本語回答するQAシステム。

---

## アーキテクチャ

```
[GCS] → [Cloud Run Job: Ingestion] → [BigQuery + Elasticsearch(kuromoji)]
                                              ↓
[ユーザー] → [Cloud Run Service: FastAPI + React] → [ハイブリッド検索 → Gemini回答]
```

---

## ディレクトリ構成

```
├── src/
│   ├── api/                # QA API（FastAPI + SPA配信）
│   ├── frontend/           # React TypeScript フロントエンド（Vite）
│   ├── ingestion/          # ドキュメント取込パイプライン
│   └── pipeline/           # Vertex AI Pipeline（RAG評価）
├── shared/                 # 共通ライブラリ（config.py + core.py）
├── scripts/
│   ├── eval/               # RAG品質評価（Recall@K / MRR / Exact Match / ROUGE-L）
│   ├── monitor/            # 監視スクリプト
│   ├── ops/                # 運用スクリプト
│   └── setup/              # 環境構築スクリプト + シェルスクリプト
├── terraform/modules/      # IaC（data / compute / elastic / registry / iam）
├── env/
│   ├── config/application.yml  # プロジェクト設定（非シークレット）
│   └── secret/credentials.yml  # クレデンシャル（git管理外）
├── data/sample/            # サンプル社内規定
└── docs/                   # 仕様・設計書・運用マニュアル
```

---

## 使い方

### 全環境構築（これだけで動く）

```bash
gcloud init                        # GCP 認証（初回のみ）
vi env/secret/credentials.yml      # クレデンシャル配置（初回のみ）
vi terraform/terraform.tfvars      # Terraform 変数配置（初回のみ）

make deploy-all                    # 全自動構築（冪等）
make destroy-all                   # 全削除（課金停止）
```

### QAクエリ

```bash
python3 scripts/ops/query.py "有給休暇の申請手続きを教えてください"
```

または QA API の URL にブラウザでアクセス（React UI）。

### RAG品質評価

```bash
make eval                  # hybrid検索で評価実行
make eval-search-patterns  # vector / ES / hybrid 3パターン比較
```

### テスト

```bash
make test      # 全テスト実行（69件）
make help      # コマンド一覧
```

### フロントエンド開発

```bash
cd src/frontend && npm run dev     # Vite dev server（API は 8080 にプロキシ）
cd src/frontend && npm run build   # ビルド → src/api/static/ に出力
```



https://github.com/user-attachments/assets/8d24cc27-797a-4fbd-bc0e-c41276a3b769


