########################################
## dev
########################################

resource "google_pubsub_topic" "dev" {
  name = "dev"
}

########################################
## reddit_links
########################################

resource "google_pubsub_topic" "reddit_links" {
  name = "reddit_links"
}