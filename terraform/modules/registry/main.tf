# コン���ナレジストリ: Artifact Registry

resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = var.repo_name
  format        = "DOCKER"
  description   = "Doc QA Docker repository"
}
