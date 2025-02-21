terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "5.14.0"
    }
  }
  backend "s3" {
    bucket = "your-bucket-tfstate" # change this to your environment
    key    = "detection_deployment-state"
    region = "us-east-1"
  }
}


provider "aws" {
    region = var.region
    #profile = var.profile

    default_tags {
      tags = {
        project = "Detection Deployment"
      }
    }
}