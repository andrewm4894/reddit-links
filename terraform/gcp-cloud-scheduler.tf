############################################################
## dev
############################################################

resource "google_cloud_scheduler_job" "dev" {
  name     = "dev"
  schedule = "0 18 * * *"
  pubsub_target {
    topic_name = google_pubsub_topic.dev.id
    # data to pass to function being called
    data = base64encode("{\"example_key\":\"example_value\"}")
  }
}