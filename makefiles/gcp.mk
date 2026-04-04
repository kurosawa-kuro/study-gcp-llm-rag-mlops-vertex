# === GCPセットアップ ===
TF_SA := terraform@$(PROJECT_ID).iam.gserviceaccount.com

.PHONY: gcp-setup-docker gcp-setup-apis gcp-setup-sa

gcp-setup-apis:
	gcloud services enable \
	  artifactregistry.googleapis.com \
	  run.googleapis.com \
	  compute.googleapis.com \
	  iam.googleapis.com \
	  cloudresourcemanager.googleapis.com \
	  cloudscheduler.googleapis.com \
	  bigquery.googleapis.com \
	  aiplatform.googleapis.com \
	  --project=$(PROJECT_ID)

COMPUTE_SA := $(shell gcloud projects describe $(PROJECT_ID) --format='value(projectNumber)')-compute@developer.gserviceaccount.com

gcp-setup-sa:
	gcloud projects add-iam-policy-binding $(PROJECT_ID) \
	  --member="serviceAccount:$(TF_SA)" \
	  --role="roles/editor" --quiet
	gcloud projects add-iam-policy-binding $(PROJECT_ID) \
	  --member="serviceAccount:$(TF_SA)" \
	  --role="roles/run.admin" --quiet

gcp-setup-vertex:  ## Vertex AI Pipeline 用セットアップ（compute SA に aiplatform.user 付与）
	gcloud projects add-iam-policy-binding $(PROJECT_ID) \
	  --member="serviceAccount:$(COMPUTE_SA)" \
	  --role="roles/aiplatform.user" --quiet

gcp-setup-docker:
	gcloud auth configure-docker $(REGION)-docker.pkg.dev

gcp-setup: gcp-setup-apis gcp-setup-sa gcp-setup-vertex gcp-setup-docker
