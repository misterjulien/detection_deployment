# Date: 20230829
# Author: Eric Julien

resource "aws_ssm_parameter" "detection_deployment_github_pat" {
  #name  = "detection_deployment_github_pat"
  name  = var.github_detection_key_name
  type  = "SecureString"
  value = var.github_detection_key

  tags = {
    project = "detection_deployment"
  }
}

resource "aws_ssm_parameter" "detection_deployment_splunk_token" {
  name  = "detection_deployment_splunk_token"
  type  = "SecureString"
  value = var.splunk_token

  tags = {
    project = "detection_deployment"
  }
}