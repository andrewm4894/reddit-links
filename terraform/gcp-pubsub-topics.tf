########################################
## reddit_links
########################################

resource "google_pubsub_topic" "reddit_links" {
  name = "reddit_links"
}