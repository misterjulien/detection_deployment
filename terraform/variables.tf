variable "region" {
    default = "us-east-1"
}

#variable "profile" {
#    default = "default"
#}

variable "bucket" {
    default = ""
}

variable "github_detection_repo" {
    default = "misterjulien/detection_library_poc"
}

variable "github_detection_key_name" {
    default = "detection_deployment_github_pat"
}

# Update this
variable "github_detection_key" {
    default = ""
}

variable "splunk_domain" {
    default = "my.splunk.com"
}

variable "splunk_port" {
    default = 8089
}

# Put your github PAT here
variable "splunk_token_name" {
    default = ""
}

# Put your Splunk token here
variable "splunk_token" {
    default = "asfgrthdfgd"
}

variable "github_base_branch" {
    default = "main"
}