resource "aws_iam_user" "honey_data" {
  name = "honey-data-bot"
}

data "aws_iam_policy_document" "honey_data" {
  statement {
    sid     = "S3DataUpload"
    actions = ["s3:PutObject"]
    resources = [
      "${aws_s3_bucket.honey_data.arn}/${local.incoming_rotations_path}/*",
      "${aws_s3_bucket.honey_data_public.arn}/*",
    ]
  }

  # https://docs.amazonaws.cn/en_us/athena/latest/ug/federated-query-iam-access.html
  statement {
    sid = "AthenaS3Results"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:AbortMultipartUpload",
      "s3:ListMultipartUploadParts"
    ]
    resources = [
      "${aws_s3_bucket.honey_data.arn}/${local.athena_results_path}/*",
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
