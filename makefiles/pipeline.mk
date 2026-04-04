# === Vertex AI Pipeline ===
PIPELINE_DIR := src/pipeline

.PHONY: pipeline-install pipeline-compile pipeline-run pipeline-run-async pipeline-status pipeline-clean

pipeline-install:  ## Pipeline 依存パッケージインストール
	pip install -q -r $(PIPELINE_DIR)/requirements.txt

pipeline-compile: pipeline-install  ## Pipeline コンパイル（pipeline.json 生成）
	cd $(PIPELINE_DIR) && python3 run_pipeline.py compile

pipeline-run: pipeline-install  ## Pipeline コンパイル & Vertex AI で実行（同期）
	cd $(PIPELINE_DIR) && python3 run_pipeline.py run

pipeline-run-async: pipeline-install  ## Pipeline コンパイル & Vertex AI で実行（非同期）
	cd $(PIPELINE_DIR) && python3 run_pipeline.py run --async

pipeline-status:  ## Pipeline 実行履歴を表示
	gcloud ai custom-jobs list \
	  --region=$(REGION) \
	  --project=$(PROJECT_ID) \
	  --limit=5

pipeline-clean:  ## Vertex AI Endpoint / Model を全削除（冪等）
	python3 scripts/reset_all.py clean-vertex
