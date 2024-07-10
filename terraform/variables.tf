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
    default = ""
}

variable "github_detection_key" {
    default = ""
}

variable "splunk_domain" {
    default = "my.splunk.com"
}

variable "splunk_port" {
    default = 8089
}

variable "splunk_token_name" {
    default = ""
}

variable "splunk_token" {
    default = ""
}

variable "github_base_branch" {
    default = "main"
}