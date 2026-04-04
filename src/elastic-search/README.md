# Elasticsearch Hello World

Elastic Cloud への接続確認用。疎通確認・ドキュメント投入・検索・クリーンアップを実行する。

## ファイル構成

```
src/elastic-search/
├── main.py              # メインスクリプト
├── requirements.txt     # 依存パッケージ
├── Dockerfile           # コンテナ実行用
├── .dockerignore        # ビルド除外設定
├── Makefile             # タスクランナー（scripts/ を参照）
├── .env                 # 接続情報（git管理外）
├── README.md
└── README 運用.md        # 運用手順
```

**NOTE**:
- Terraform定義 → プロジェクトルートの `terraform/elastic.tf` に統合済み
- オペレーションスクリプト → プロジェクトルートの `scripts/es_*.py` に統合済み

## セットアップ

### 1. 設定ファイルの作成

`.env` に接続情報を記載する。

```
# Elastic Cloud
ELASTIC_CLOUD_URL=https://<your-cloud-url>:443
ELASTIC_API_KEY=<ES接続用APIキー>
ELASTIC_CLOUD_API_KEY=<Elastic Cloud Org APIキー>
```

### 2. 初期化

```bash
make install       # 依存パッケージインストール
make auth-docker   # Docker認証設定
```

## ローカル実行

```bash
make run        # ローカル実行（.envから直接読み込み）
```

## コマンド一覧

```bash
make help
```
