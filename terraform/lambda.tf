# This is for creating the detection deployment AWS Lambda.
# Date: 20230829
# Author: Eric Julien

data "archive_file" "lambda" {
  type        = "zip"
  source_dir = "../lambda"
  output_path = "../detection_deployment.zip"
}

resource "aws_lambda_function" "detection_deployment_lambda" {
  # If the file is not in the current working directory you will need to include a
  # path.module in the filename.
  description   = "Regulary scan the detection library and add/update detections in security tools."
  filename      = "../detection_deployment.zip"
  function_name = "detection_deployment_lambda"
  role          = aws_iam_role.detection_deployment_lambda_role.arn
  handler       = "detection_deployment.lambda_handler"
  runtime       = "python3.9"
  timeout       = "900"
  memory_size   = 256

  source_code_hash = data.archive_file.lambda.output_base64sha256

  environment {
    variables = {
        GITHUB_DETECTION_REPO = var.github_detection_repo
        GITHUB_DETECTION_KEY_NAME = var.github_detection_key_name
        GITHUB_BASE_BRANCH = var.github_base_branch
        DYNAMODB_DETECTION_REPO_TABLE = aws_dynamodb_table.detection_repo_tracker.name
        DYNAMODB_DETECTION_FILE_TABLE = aws_dynamodb_table.detection_file_tracker.name
        SPLUNK_HOST_AND_PORT = "${var.splunk_domain}:${var.splunk_port}"
        SPLUNK_TOKEN_NAME = var.splunk_token_name
    }
  }
}
