resource "aws_s3_bucket" "honey_data" {
  bucket = "honey-data"
  acl    = "private"
}

resource "aws_s3_bucket_public_access_block" "honey_data_block" {
  bucket = aws_s3_bucket.honey_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket" "honey_data_public" {
  bucket = "honey-data-public"
  acl    = "public-read"

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["https://honey.fitness"]
    max_age_seconds = 300
  }
}
