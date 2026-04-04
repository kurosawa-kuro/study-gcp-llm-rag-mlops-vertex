# Elasticsearch Hello World

Elastic Cloud への接続確認用。疎通確認・ドキュメント投入・検索・クリーンアップを実行する。

## ファイル構成

```
src/elastic-search/
├── main.py              # メインスクリプト
├── requirements.txt     # 依存パッケージ
├── Dockerfile           # コンテナ実行用
├── .dockerignore        # ビルド除外設定
├── Makefile             # タスクランナー（scriptsを呼び出す薄いラッパー）
├── .env                 # 全設定値・認証情報（git管理外・唯一の定義元）
├── README.md
├── README 運用.md        # 運用手順
├── scripts/             # オペレーション用Pythonスクリプト
│   ├── config.py            # 共通設定・ユーティリティ
│   ├── docker_ops.py        # Docker操作（build, push, clean）
│   ├── gcp_ops.py           # GCP操作（execute, logs）
│   └── tf_ops.py            # Terraform操作（init, plan, apply, destroy, import）
└── terraform/           # IaC定義
    ├── providers.tf         # プロバイダ設定 (elastic/ec, google)
    ├── variables.tf         # 変数定義
    ├── main.tf              # リソース定義
    └── outputs.tf           # 出力値
```

## セットアップ

### 1. 設定ファイルの作成

`.env` に全設定値・認証情報を記載する（唯一の定義元）。

```
# GCP
PROJECT_ID=mlops-dev-a
REGION=asia-northeast1

# Elastic Cloud
DEPLOYMENT_NAME=hello-elastic
ELASTIC_CLOUD_URL=https://<your-cloud-url>:443
ELASTIC_API_KEY=<ES接続用APIキー>
ELASTIC_CLOUD_API_KEY=<Elastic Cloud Org APIキー>

# Cloud Run Job
JOB_NAME=hello-elastic-job
REPO_NAME=hello-elastic-repo
SECRET_NAME=hello-elastic-api-key
```

### 2. 初期化

```bash
make install       # 依存パッケージインストール
make tf-init       # Terraformプロバイダ初期化
make auth-docker   # Docker認証設定
```

## デプロイ

### 全構築（infra → push → job）

```bash
make deploy-all
```

### 全削除（課金停止）

```bash
make destroy-all
```

### ジョブ実行・ログ確認

```bash
make execute    # Cloud Run Job 実行
make logs       # ログ確認
```

## ローカル実行

```bash
make run        # ローカル実行（.envから直接読み込み）
make docker-run # Docker実行
```

## アーキテクチャ

```
[WSL]                        [GCP]                         [Elastic Cloud]
  │                            │                               │
  ├─ make deploy-all           │                               │
  │   ├─ tf-apply-infra ──────►├─ Artifact Registry            │
  │   │                        ├─ Secret Manager               │
  │   │                        │                          ┌────┤
  │   │                        │                          │ EC deployment
  │   │                        │                          │ (ES + Kibana)
  │   ├─ push ────────────────►├─ Docker image            │
  │   └─ tf-apply ────────────►├─ Cloud Run Job ─────────►│
  │                            │                          │
  ├─ make execute ────────────►├─ Job実行 ───────────────►│ ES接続・検索
  └─ make logs ◄───────────────┘                          └────┘
```

## リソース構成（Terraform管理）

| リソース | Terraform resource | 名前 |
|---|---|---|
| Elastic Cloud デプロイメント | `ec_deployment` | `hello-elastic` |
| Artifact Registry | `google_artifact_registry_repository` | `hello-elastic-repo` |
| Secret Manager | `google_secret_manager_secret` / `_version` | `hello-elastic-api-key` |
| IAM (Secret アクセス権) | `google_secret_manager_secret_iam_member` | — |
| Cloud Run Job | `google_cloud_run_v2_job` | `hello-elastic-job` |

## コマンド一覧

```bash
make help
```

## 実行結果（例）

```
=== 1. info ===
cluster_name: 4c4c544a5e0949bf9100801dffafda9b
version: 9.3.2

=== 2. index document ===
result: created
_id: o3MXUp0BzeEEjc3ElQCP

=== 3. search ===
total hits: 1
  -> {'message': 'hello world', 'tag': 'test'}

=== 4. cleanup ===
index deleted
```
