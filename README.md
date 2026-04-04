
# 社内ドキュメント検索・QAシステム

GCSにドキュメントをアップロードするだけでAIが根拠ドキュメント付きで日本語回答するQAシステム。

---

## アーキテクチャ

```
[GCS] → [Cloud Run Job: Ingestion] → [BigQuery + Elasticsearch]
                                              ↓
[ユーザー] → [Cloud Run Service: QA API] → [ハイブリッド検索 → Gemini回答]
```

---

## ディレクトリ構成

```
├── src/doc-qa/
│   ├── common/             # 共有ライブラリ（config.py + core.py）
│   ├── ingestion/          # ドキュメント取込パイプライン
│   └── api/                # QA API（FastAPI）
├── scripts/
│   ├── eval/               # RAG品質評価（Recall@K / MRR / Exact Match / ROUGE-L）
│   └── ...                 # 運用スクリプト（monitor / ops / setup）
├── terraform/modules/      # IaC（data / compute / elastic / registry / iam）
├── env/
│   ├── config/application.yml  # プロジェクト設定（非シークレット）
│   └── secret/credentials.yml  # クレデンシャル（git管理外）
├── data/sample/            # サンプル社内規定
└── docs/                   # 仕様・設計書
```

---

## 使い方

### 初回セットアップ

```bash
python3 scripts/setup/gcp.py       # 未インストール時のみ実行
python3 scripts/setup/terraform.py  # 未インストール時のみ実行
gcloud config list                  # 設定済みか確認（未設定なら gcloud init）
make gcp-setup
make tf-apply
```

### ドキュメント取込 → QAクエリ

```bash
python3 scripts/ops/upload_doc.py data/sample/
make ingestion-run
python3 scripts/ops/query.py "有給休暇の申請手続きを教えてください"
```

### RAG品質評価

```bash
make eval                  # hybrid検索で評価実行
make eval-baseline         # ベースライン記録
make eval-search-patterns  # vector / ES / hybrid 3パターン比較
```

### デプロイ・テスト

```bash
make deploy    # 全体デプロイ
make test      # 全テスト実行
make help      # コマンド一覧
```
