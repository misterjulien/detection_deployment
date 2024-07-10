# Date: 20230829
# Author: Eric Julien

resource "aws_dynamodb_table" "detection_repo_tracker" {
    #provider         = aws.main
    name             = "detection_repo_tracker"
    hash_key         = "Repo"
    stream_enabled   = true
    stream_view_type = "NEW_AND_OLD_IMAGES"
    read_capacity  = 20
    write_capacity = 20

    attribute {
        name = "Repo"
        type = "S"
    }
    #attribute {
    #    name = "last_commit"
    #    type = "S"
    #}

    tags = {
        project = "detection_deployment"
    }
}

resource "aws_dynamodb_table" "detection_file_tracker" {
    #provider         = aws.main
    name             = "detection_file_tracker"
    hash_key         = "filename"
    stream_enabled   = true
    stream_view_type = "NEW_AND_OLD_IMAGES"
    read_capacity  = 20
    write_capacity = 20

    attribute {
        name = "filename"
        type = "S"
    }

    tags = {
        project = "detection_deployment"
    }
}

