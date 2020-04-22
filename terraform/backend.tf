terraform {
  backend "gcs" {
    bucket = "andrewm4894-reddit-links-tf-state"
    prefix = "terraform/state"
  }
}