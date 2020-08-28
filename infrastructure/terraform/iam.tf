resource "aws_iam_user" "honey_data" {
  name = "honey-data-bot"
}

resource "aws_iam_access_key" "honey_data" {
  user    = aws_iam_user.honey_data.name
  pgp_key = var.pgp_key
}

data "aws_iam_policy_document" "honey_data" {
  statement {
    sid = "AthenaS3Metadata"
    actions = [
      "s3:ListBucket",
      "s3:GetBucketLocation",
      "s3:ListAllMyBuckets"
    ]
    resources = ["*"]
  }

  statement {
    sid = "AthenaS3Access"
    actions = [
      "s3:GetBucketLocation",
      "s3:GetObject",
      "s3:ListBucket",
      "s3:ListBucketMultipartUploads",
      "s3:ListMultipartUploadParts",
      "s3:AbortMultipartUpload",
      "s3:PutObject"
    ]
    resources = [
      "${aws_s3_bucket.honey_data.arn}/${local.incoming_rotations_path}*",
      "${aws_s3_bucket.honey_data.arn}/${local.athena_results_path}*",
      "${aws_s3_bucket.honey_data_public.arn}*",
    ]
  }

  # https://docs.aws.amazon.com/athena/latest/ug/example-policies-workgroup.html#example3-user-access
  statement {
    sid = "AthenaMetadata"
    actions = [
      "athena:ListWorkGroups",
      "athena:GetExecutionEngine",
      "athena:GetExecutionEngines",
      "athena:GetNamespace",
      "athena:GetCatalogs",
      "athena:GetNamespaces",
      "athena:GetTables",
      "athena:GetTable"
    ]
    resources = ["*"]
  }

  statement {
    sid = "AthenaExecution"
    actions = [
      "athena:StartQueryExecution",
      "athena:GetQueryResults",
      "athena:DeleteNamedQuery",
      "athena:GetNamedQuery",
      "athena:ListQueryExecutions",
      "athena:StopQueryExecution",
      "athena:GetQueryResultsStream",
      "athena:ListNamedQueries",
      "athena:CreateNamedQuery",
      "athena:GetQueryExecution",
      "athena:BatchGetNamedQuery",
      "athena:BatchGetQueryExecution",
      "athena:GetWorkGroup"
    ]
    resources = [
      aws_athena_workgroup.honey_data.arn
    ]
  }

  statement {
    sid = "AthenaGlueExecution"
    actions = [
      "glue:GetTable",
      "glue:GetPartition",
      "glue:GetPartitions",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "honey_data" {
  name        = "honey-data-policy"
  description = "Policy to allow upload and processing for the honey.data pipeline"
  policy      = data.aws_iam_policy_document.honey_data.json
}

resource "aws_iam_user_policy_attachment" "honey_data" {
  user       = aws_iam_user.honey_data.name
  policy_arn = aws_iam_policy.honey_data.arn
}
