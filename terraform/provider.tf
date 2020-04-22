provider "google" {
  credentials = file(var.gcp_terraform_service_account_json_path)
  project     = var.gcp_project_id
  region      = var.gcp_region
  zone        = var.gcp_zone
}