resource "aws_athena_workgroup" "honey_data" {
  name = "honey-data"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.honey_data.id}/${local.athena_results_path}/"
    }
  }
}
