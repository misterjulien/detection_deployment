# Date: 20230829
# Author: Eric Julien

resource "aws_iam_role" "detection_deployment_lambda_role" {
    name               = "detection_deployment_lambda_role"
    assume_role_policy = data.aws_iam_policy_document.detection_deployment_assume_policy.json

    tags = {
        project = "detection_deployment"
    }
}

data "aws_iam_policy_document" "detection_deployment_assume_policy" {
    statement {
        principals  {
            type        = "Service"
            identifiers = ["lambda.amazonaws.com"]
        }
        actions = ["sts:AssumeRole"]
    }
    #statement {
    #    actions = [
    #        "ssm:GetParameter",
    #    ]
    #    resources = [
    #        aws_ssm_parameter.detection_deployment_github_pat.arn
    #    ]
    #}
}


resource "aws_iam_role_policy" "detection_deployment_lambda_role_policy" {
    name    = "detection_deployment_lambda_role"
    role    = aws_iam_role.detection_deployment_lambda_role.id
    policy  = jsonencode({
        Version= "2012-10-17"
        Statement= [
            {
                Action= [
                    "ssm:GetParameters",
                    "ssm:GetParameter",
                ],
                Effect = "Allow",
                Resource = [
                    aws_ssm_parameter.detection_deployment_github_pat.arn,
                    aws_ssm_parameter.detection_deployment_splunk_token.arn
                ]
            },
            {
                Action = [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ]
                Effect = "Allow"
                Resource = ["*"]
            },
            {
                Action = [
                    "dynamodb:BatchGetItem",
                    "dynamodb:GetItem",
                    "dynamodb:Query",
                    "dynamodb:Scan",
                    "dynamodb:BatchWriteItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem"
                ]
                Effect = "Allow"
                Resource = [
                    aws_dynamodb_table.detection_repo_tracker.arn,
                    aws_dynamodb_table.detection_file_tracker.arn
                ]
            },
        ]
    })
}
