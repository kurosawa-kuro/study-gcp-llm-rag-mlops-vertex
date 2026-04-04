# 運用手順

## 前提

- `make tf-init` でTerraform初期化済み
- `make auth-docker` でDocker認証設定済み

## 1. 全構築（初回 or destroy後）

```bash
# Step 1: .env を準備（初回は既存値でOK）
# Step 2: インフラ構築＆イメージpush＆Cloud Run Job作成
make deploy-all
```

**deploy-all 完了後、必ず以下を実施：**

```bash
# Step 3: Terraform出力からELASTIC_CLOUD_URLを確認
#   出力例: elasticsearch_endpoint = "https://xxxx.asia-northeast1.gcp.cloud.es.io:443"
#   ※ デプロイごとにURLが変わるため、必ず確認

# Step 4: Kibana（Elastic Cloudコンソール → Open Kibana）でAPIキーを発行
#   Management → API Keys → Create API key

# Step 5: .env を更新
#   ELASTIC_CLOUD_URL=<Step 3の値>
#   ELASTIC_API_KEY=<Step 4の値>

# Step 6: Secret Managerに新しいAPIキーを反映
make tf-apply

# Step 7: 動作確認
make execute
make logs
```

**なぜこの手順が必要か：**
- Elastic Cloudデプロイメントは毎回新しいURLが割り当てられる
- APIキーはデプロイメント固有。古いキーでは認証失敗する
- Cloud Run JobはSecret Manager経由でAPIキーを取得するため、.envだけでなくSecret Managerも更新が必要

## 2. 全削除（課金停止）

```bash
make destroy-all
```

## 3. コード更新時（インフラ変更なし）

```bash
make push       # イメージ再ビルド＆push
make execute    # 実行確認
```

.env の変更は不要。

## 4. APIキー更新時（デプロイメント変更なし）

```bash
# 1. Kibana で新しいAPIキーを発行
# 2. .env の ELASTIC_API_KEY を更新
# 3. Secret Managerに反映
make tf-apply
# 4. 動作確認
make execute
```

**注意：** .env を更新しただけでは Cloud Run Job に反映されない。`make tf-apply` で Secret Manager を更新する必要がある。

## 5. ローカル開発

```bash
make install    # 依存パッケージインストール
make run        # ローカル実行（.envから直接読み込み）
make docker-run # Docker実行
```

ローカル実行は .env を直接読むため、Secret Manager の更新は不要。

## 設定管理

全設定値は `.env` で一元管理。

```
.env
├── GCP:          PROJECT_ID, REGION
├── Elastic Cloud: DEPLOYMENT_NAME, ELASTIC_CLOUD_URL, ELASTIC_API_KEY, ELASTIC_CLOUD_API_KEY
└── Cloud Run Job: JOB_NAME, REPO_NAME, SECRET_NAME
```

| 設定 | 変更タイミング |
|------|--------------|
| `ELASTIC_CLOUD_URL` | deploy-all のたびに更新（デプロイごとにURLが変わる） |
| `ELASTIC_API_KEY` | deploy-all のたびに再発行＋更新 |
| `ELASTIC_CLOUD_API_KEY` | Elastic Cloud Org APIキー。変更不要（Org共通） |
| その他 | 基本的に固定 |

## .env 更新後の反映先

| 操作 | 反映先 |
|------|--------|
| `make run` / `make docker-run` | .env を直接読む → 即反映 |
| `make tf-apply` | Secret Manager を更新 → Cloud Run Job に反映 |
| `make push` | イメージ再ビルド（.env の値はイメージに含まない） |

## Makeコマンド一覧

```bash
make help
```

| コマンド | 用途 |
|---------|------|
| `make deploy-all` | 全構築（infra → push → job） |
| `make destroy-all` | 全削除（terraform destroy → docker clean） |
| `make execute` | Cloud Run Job 実行 |
| `make logs` | ログ確認 |
| `make push` | イメージ再ビルド＆push |
| `make run` | ローカル実行 |
| `make tf-apply` | Terraform適用（設定変更の反映） |
| `make tf-plan` | 差分確認 |
