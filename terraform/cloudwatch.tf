# Date: 20230829
# Author: Eric Julien

resource "aws_lambda_permission" "detection_deployment_allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.detection_deployment_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.detection_deployment_cloudwatch_trigger_rule.arn
}

resource "aws_cloudwatch_event_rule" "detection_deployment_cloudwatch_trigger_rule" {
    name        = "detection_deployment_cloudwatch_trigger_rule"
    schedule_expression = "cron(5 1 * * ? *)"
}

resource "aws_cloudwatch_event_target" "detection_deployment_cloudwatch-trigger_target" {
  rule      = aws_cloudwatch_event_rule.detection_deployment_cloudwatch_trigger_rule.name
  arn       = aws_lambda_function.detection_deployment_lambda.arn
}