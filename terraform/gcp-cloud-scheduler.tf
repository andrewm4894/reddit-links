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


############################################################
## redditlinks_machinelearning
############################################################

resource "google_cloud_scheduler_job" "redditlinks_machinelearning" {
  name     = "redditlinks_machinelearning"
  schedule = "0 18 * * *"
  pubsub_target {
    topic_name = google_pubsub_topic.redditlinks.id
    # data to pass to function being called
    data = base64encode("{\"subreddit\":\"machinelearning\",\"time_filter\":\"hour\",\"comments_max\":100,\"airtable_base\":\"appYRlbpZ7tlQnmbg\",\"airtable_table\":\"all-links\"}")
  }
}