########################################
## dev
########################################

resource "google_pubsub_topic" "dev" {
  name = "dev"
}

########################################
## redditlinks
########################################

resource "google_pubsub_topic" "redditlinks" {
  name = "redditlinks"
}