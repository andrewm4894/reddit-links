########################################
## dev
########################################

variable "pyfunc_info_dev" {
  type = map(string)
  default = {
    name    = "dev"
    version = "v2"
  }
}

# zip up our source code
data "archive_file" "pyfunc_zip_dev" {
  type        = "zip"
  source_dir  = "${path.root}/python-functions/${var.pyfunc_info_dev.name}/"
  output_path = "${path.root}/python-functions/zipped/${var.pyfunc_info_dev.name}_${var.pyfunc_info_dev.version}.zip"
}

# create the storage bucket
resource "google_storage_bucket" "pyfunc_dev" {
  name = "pyfunc_${var.pyfunc_info_dev.name}"
}

# place the zip-ed code in the bucket
resource "google_storage_bucket_object" "pyfunc_zip_dev" {
  name   = "${var.pyfunc_info_dev.name}_${var.pyfunc_info_dev.version}.zip"
  bucket = google_storage_bucket.pyfunc_dev.name
  source = "${path.root}/python-functions/zipped/${var.pyfunc_info_dev.name}_${var.pyfunc_info_dev.version}.zip"
}

# define the function resource
resource "google_cloudfunctions_function" "pyfunc_dev" {
  name                  = var.pyfunc_info_dev.name
  description           = "dev"
  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.pyfunc_dev.name
  source_archive_object = google_storage_bucket_object.pyfunc_zip_dev.name
  entry_point           = "dev"
  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = google_pubsub_topic.dev.id
  }
  timeout = 120
  runtime = "python37"
  environment_variables = {
  }
}

# IAM entry for all users to invoke the function
resource "google_cloudfunctions_function_iam_member" "pyfunc_invoker_dev" {
  project        = google_cloudfunctions_function.pyfunc_dev.project
  region         = google_cloudfunctions_function.pyfunc_dev.region
  cloud_function = google_cloudfunctions_function.pyfunc_dev.name
  role           = "roles/cloudfunctions.invoker"
  member         = "allUsers"
}


########################################
## redditlinks
########################################

variable "pyfunc_info_redditlinks" {
  type = map(string)
  default = {
    name    = "redditlinks"
    version = "v9"
  }
}

# zip up our source code
data "archive_file" "pyfunc_zip_redditlinks" {
  type        = "zip"
  source_dir  = "${path.root}/python-functions/${var.pyfunc_info_redditlinks.name}/"
  output_path = "${path.root}/python-functions/zipped/${var.pyfunc_info_redditlinks.name}_${var.pyfunc_info_redditlinks.version}.zip"
}

# create the storage bucket
resource "google_storage_bucket" "pyfunc_redditlinks" {
  name = "pyfunc_${var.pyfunc_info_redditlinks.name}"
}

# place the zip-ed code in the bucket
resource "google_storage_bucket_object" "pyfunc_zip_redditlinks" {
  name   = "${var.pyfunc_info_redditlinks.name}_${var.pyfunc_info_redditlinks.version}.zip"
  bucket = google_storage_bucket.pyfunc_redditlinks.name
  source = "${path.root}/python-functions/zipped/${var.pyfunc_info_redditlinks.name}_${var.pyfunc_info_redditlinks.version}.zip"
}

# define the function resource
resource "google_cloudfunctions_function" "pyfunc_redditlinks" {
  name                  = var.pyfunc_info_redditlinks.name
  description           = "redditlinks"
  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.pyfunc_redditlinks.name
  source_archive_object = google_storage_bucket_object.pyfunc_zip_redditlinks.name
  entry_point           = "redditlinks"
  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = google_pubsub_topic.redditlinks.id
  }
  timeout = 540
  runtime = "python37"
  environment_variables = {
    REDDIT_CLIENT_ID     = var.reddit_client_id
    REDDIT_CLIENT_SECRET = var.reddit_client_secret
    AIRTABLE_KEY         = var.airtable_key
  }
}

# IAM entry for all users to invoke the function
resource "google_cloudfunctions_function_iam_member" "pyfunc_invoker_redditlinks" {
  project        = google_cloudfunctions_function.pyfunc_redditlinks.project
  region         = google_cloudfunctions_function.pyfunc_redditlinks.region
  cloud_function = google_cloudfunctions_function.pyfunc_redditlinks.name
  role           = "roles/cloudfunctions.invoker"
  member         = "allUsers"
}