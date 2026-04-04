# === QA API（社内ドキュメント QA サービス） ===
QA_API_DIR := src/doc-qa/api
QA_API_IMAGE := $(IMAGE_BASE)/doc-qa-api:$(TAG)

.PHONY: qa-api-test qa-api-build qa-api-push qa-api-deploy qa-api-logs qa-api-url qa-api-monitor

qa-api-test:  ## QA API テスト実行
	cd $(QA_API_DIR) && python -m pytest -v test_main.py

qa-api-build:  ## QA API Docker イメージビルド
	docker build -t $(QA_API_IMAGE) $(QA_API_DIR)

qa-api-push: qa-api-build  ## QA API イメージ push
	docker push $(QA_API_IMAGE)

qa-api-deploy: qa-api-push  ## QA API 冪等デプロイ
	gcloud run services update doc-qa-api \
		--image $(QA_API_IMAGE) \
		--region $(REGION)

qa-api-logs:  ## QA API ログ確認
	gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="doc-qa-api"' \
		--limit 20 --format json

qa-api-url:  ## QA API の URL 表示
	@gcloud run services describe doc-qa-api --region $(REGION) --format 'value(status.url)'

qa-api-monitor:  ## QA API 健全性チェック + Discord 通知
	python3 scripts/monitor_qa_api.py
