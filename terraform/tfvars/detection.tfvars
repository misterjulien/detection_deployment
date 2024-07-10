#environment = "dev"
#profile = "default"


# CHANGEME: This needs to be changed to your github repo
github_detection_repo = "misterjulien/detection_library_poc"

github_detection_key_name = "detection_deployment_github_pat"

# Since the repo is public, I don't think we need this.  But if someone
# was going to use this project with a private repo then it's needed.
# CHANGEME: This needs to be changed to your github PAT, or simply use an empty string and manually
#   put it AWS SSM.
github_detection_key = "github_pat_ABCDEF1234567890"
github_base_branch = "main"

splunk_domain = "my.splunk.com"
splunk_port = 8089
splunk_token_name = "detection_deployment_splunk_token"
splunk_token = "1234567890"