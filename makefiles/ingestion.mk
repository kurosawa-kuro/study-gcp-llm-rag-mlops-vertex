# === Ingestion（ドキュメント取込パイプライン） ===
INGESTION_DIR := src/doc-qa/ingestion
INGESTION_IMAGE := $(IMAGE_BASE)/doc-qa-ingestion:$(TAG)

.PHONY: ingestion-test ingestion-build ingestion-push ingestion-deploy ingestion-run ingestion-logs

ingestion-test:  ## Ingestion テスト実行
	cd $(INGESTION_DIR) && python -m pytest -v test_main.py

ingestion-build:  ## Ingestion Docker イメージビルド
	docker build -t $(INGESTION_IMAGE) $(INGESTION_DIR)

ingestion-push: ingestion-build  ## Ingestion イメージ push
	docker push $(INGESTION_IMAGE)

ingestion-deploy: ingestion-push  ## Ingestion 冪等デプロイ
	gcloud run jobs update doc-qa-ingestion \
		--image $(INGESTION_IMAGE) \
		--region $(REGION)

ingestion-run:  ## Ingestion Cloud Run Job 実行
	gcloud run jobs execute doc-qa-ingestion --region $(REGION) --wait

ingestion-logs:  ## Ingestion 実行履歴確認
	gcloud run jobs executions list --job doc-qa-ingestion --region $(REGION) --limit 5
