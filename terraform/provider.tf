terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "5.14.0"
    }
  }
  backend "s3" {
    bucket = "your-bucket-tfstate"
    key    = "detection_deployment-state"
    region = "us-east-1"
  }
}


provider "aws" {
    # Configuration options
    #region = var.region
    #profile = var.profile
}