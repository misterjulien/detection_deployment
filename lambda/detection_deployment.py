################################
# Author: Eric Julien
# Description: This is the Lambda python code that is part of the Detection Deployment infrastructure
#   that is meant to deploy new and updated detections to security tools (eg - SIEMs).  
#   (It also removes detections from security tools.)  It helps to implements Detection-as-Code.
#   This code will deploy either 1) all detections in the detection repo or 2) only new and updated 
#   detections in the repo (default).  
#   It will also validate that the detections in the security tools match
#   what is in github. (In Progess)

import os
import boto3
import requests
import json
import base64
import yaml

################################
# Lambda event options:
#    get_all_detections - Get all the detections, not just new and updated, from the repo and deploy them.
#      Set to "True" to enable this.  All other values are equivalent to False.  The default behavior  is
#      is to only get the new and updated detections since the last update.
#    preview_only - Do everything but actually deploy detections.  Set to "True" to enable this.  All other
#      values are equivalent to False.

# TODO: We're assuming all detections go to Splunk, change so that we can deploy to multiple SIEMs 
#   and different SIEM instances (eg - a specific Splunk instance if we have multiple Splunk instances)
# TODO: Validate that the search in Splunk/SIEM matches what's is the file tracker (for 1 detection or for all detection)
# TODO: Have the ability to sync up the file tracker with what's in github.
# TODO: Document the expected format of the detection file.
# TODO: Document:
#  - Secure your detection repo to only authorized users
#  - Fit detections to your environment.  Detections are not one-size-fits-all.
#  - Mention to include Github actions to ensure proper formatting of the detection file.
#  - Mention the scope - not creating or tuning detections; log ingestion; just deploying 
#      detections with automations

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

DYNAMODB_CLIENT = boto3.client('dynamodb')
SSM_CLIENT = boto3.client('ssm')

# Get Github personal access token (PAT) from SSM
#  Parameter(s):
#  none
#
#  Returns: The Github Personal Access Token needed to authenticate to Github 
def get_github_pat() -> str:
    """ """
    try:
        github_pat = SSM_CLIENT.get_parameter(
            Name=os.environ["GITHUB_DETECTION_KEY_NAME"],
            WithDecryption=True
        )["Parameter"]["Value"]
        return github_pat
    except Exception as e:
        logger.error(f"ERROR: Unable to get Github PAT from SSM -  {e}")
        exit(1)

# Get the SHA hash from the base branch
#  Parameter(s):
#  github_pat - This is the Github Personal Access Token needed to authenticate to Github
#
#  Returns: The current SHA hash of the repo's base commit.
def get_current_commit_sha_from_github(github_pat) -> str:
    headers = {'Authorization': f'token {github_pat}'}
    try:
        current_sha = requests.get(f"https://api.github.com/repos/{os.environ['GITHUB_DETECTION_REPO']}/commits/{os.environ['GITHUB_BASE_BRANCH']}", headers=headers)
        print(f"current_sha = {current_sha.json()['sha']}")
        return current_sha.json()['sha']
    except Exception as e:
        logger.error(f"ERROR: Unable to get last commit SHA from Github -  {e}")
        exit(1)

# Get the last know SHA hash from the database
#  Parameters(s):
#  none
#
# Returns: The SHA hash found in the database for the repo.  This is the last known SHA hash
#    since detections were deployed.
def get_last_commit_sha_from_db() -> str:
    try:
        item_response = DYNAMODB_CLIENT.get_item(
            TableName=os.environ['DYNAMODB_DETECTION_REPO_TABLE'],
            Key = {
                'Repo': {'S': os.environ["GITHUB_DETECTION_REPO"]}
            }
        )
        last_commit_sha = item_response.get('Item', {}).get('last_commit_sha', {}).get('S', '')
        print(f"last_commit_sha = {last_commit_sha}")
        return last_commit_sha
    except Exception as e:
        logger.error(f"ERROR: Unable to get Dynamodb item -  {e}")
        exit(1)

# Compare the current SHA hash with the SHA hash that was last seen in database
#  Parameter(s):
#  current_sha - The current SHA hash of the repo's base commit.
#  last_sha - The SHA hash found in the database for the repo.  This is the last known SHA hash
#    since detections were deployed. 
#
#  Returns: 0 if the they are the same, 1 if different
def compare_sha_values(current_sha, last_sha) -> int:
    if current_sha == last_sha:
        logger.info(f"INFO: No new or updated detections to deploy")
        return 0
    else:
        logger.info(f"INFO: Changes to repo")
        return 1

# Insert a new item in the database with the repo and SHA
#  Parameter(s):
#  commit_sha - This is the SHA hash of the Github commit
#
#  Returns: None 
def put_commit_sha_in_detection_repo_table(commit_sha) -> None:
    try:
        put_item_response = DYNAMODB_CLIENT.put_item(
            TableName=os.environ['DYNAMODB_DETECTION_REPO_TABLE'],
            Item = {
                'Repo': {'S': os.environ['GITHUB_DETECTION_REPO']},
                'last_commit_sha': {'S': commit_sha}
            }
        )
        # Check for successful put_item
        # It's possible for put_item() to connect and still be unsuccessful, so that's why we have this.
        if put_item_response.get('ResponseMetadata', {}).get('HTTPStatusCode', "") == 200:
            logger.info(f"INFO: dynamodb successfully updated with new SHA item")
        else:
            logger.error(f"ERROR: dynamodb NOT updated with new SHA item")
        return 
    except Exception as e:
        logger.error(f"ERROR: Unable to update detection repo table with new SHA -  {e}")
        exit(1)

# Get a list of new and updated detections from Github
def get_new_and_updated_detections_from_github(github_pat, current_sha, last_known_sha) -> list:
    headers = {'Authorization': f'token {github_pat}'}
    file_list = []
    try:
        #response = requests.get(f"https://api.github.com/repos/{os.environ['GITHUB_DETECTION_REPO']}/commits/{current_sha}", headers=headers)
        response = requests.get(f"https://api.github.com/repos/{os.environ['GITHUB_DETECTION_REPO']}/compare/{last_known_sha}...{current_sha}", headers=headers)
        files = response.json().get('files', [])
        for file in files:
            # Only get the detection files
            if (file.get('filename', '').endswith('.yml')):
                file_list.append(file)
                logger.info(f"INFO: detection file - {file.get('filename', '')}")
        return file_list
    except Exception as e:
        logger.error(f"ERROR: Unable to get new and updated detections from github -  {e}")
        exit(1)

def get_detection_file_metadata(github_pat, file_url) -> dict:
    try:
        # Get the 'content' field from the response, 'content' here is from requests.get(), not the file 'contents'
        headers = {'Authorization': f'token {github_pat}'}
        file_response = requests.get(file_url, headers=headers )
        file_response_json = json.loads(file_response.content)
        return file_response_json
    except Exception as e:
        logger.error(f"ERROR: Unable to get raw file contents from github -  {e}")
        return {}

def get_detection_file_contents(file_response_json) -> str:
    try:
        # Get the contents of the actual file
        file_contents = file_response_json.get('content', '')
        encoding_type = file_response_json.get('encoding', '')
        #filename_and_path = file_response_json.get('path', '')
        if encoding_type == "base64": 
            detection_file = base64.b64decode(file_contents).decode('utf-8')
        else:
            # Not sure what to do if it's not base64
            logger.info(f"INFO: detection file is encoded with something other than base64")
        return detection_file
    except Exception as e:
        logger.error(f"ERROR: decoding file_contents -  {e}")
        return ""

def get_splunk_search(detection_file) -> str:
    try:
        splunk_search = yaml.safe_load(detection_file).get('detection', '').get('splunk', '') 
        return splunk_search
    except Exception as e:
        logger.error(f"ERROR: Unable to get Splunk search from detection file -  {e}")
        return ""

def get_splunk_token():
    try:
        splunk_token = SSM_CLIENT.get_parameter(
            Name=os.environ["SPLUNK_TOKEN_NAME"],
            WithDecryption=True
        )["Parameter"]["Value"]
        return splunk_token
    except Exception as e:
        logger.error(f"ERROR: Unable to get Splunk token from SSM -  {e}")
        return ""
        
def deploy_detection_to_splunk(filename_and_path, detection_file, event):
    ### TODO: Test to make sure this works

    try:
        title = yaml.safe_load(detection_file).get('title', '')
        splunk_search = yaml.safe_load(detection_file).get('detection', '').get('splunk', '') 
        description = yaml.safe_load(detection_file).get('description', '')
    except Exception as e:
        logger.error(f"ERROR: Unable to get values from detection file -  {e}")
        return ""
    
    if not event.get('preview_only', ''):
        print("Deploying detection to Splunk")
        
        splunk_url = f"https://{os.environ['SPLUNK_HOST_AND_PORT']}/services/saved/searches"
        headers = {
            "Authorization": f"Bearer {get_splunk_token()}",
            "Content-Type": "application/xml"
        }
        payload = {
            'search': splunk_search, # Required
            "name": title, # Required 
            "description": description, 
        }
        try:
            response = requests.post(splunk_url, headers=headers, data=payload, verify=False)
            
            if response.status_code == 201:
                print("Splunk search created successfully")
                search_id = response.text.strip()
                #What is 'search_id'? Do we need to add it to the file_tracker_table?
                return search_id
            else:
                logger.error(f"ERROR: Failed to create Splunk search. Status code: {response.status_code}")
                logger.error(response.text)
                return ""
        except Exception as e:
            logger.error(f"ERROR: Unable to deploy detection search to Splunk -  {e}")
            return ""
    else:
        print("Deploying detection to Splunk (Preview Only)")

    print(f"filename_and_path = {filename_and_path}")
    print(f"splunk_search = {splunk_search}")
    # Should we return something else here?
    return True

def remove_detection_from_splunk(filename_and_path):
    print("Removing detection from Splunk")
    print(f"filename_and_path = {filename_and_path}")
    # TODO: Replace the above with actually removing from Splunk

def remove_from_file_tracker():
    pass

def update_file_tracker_item(path, sha, search) -> None:
    try:
        # Check if the 'path' already exists, does it overwrite it or does it create a new entry
        put_item_response = DYNAMODB_CLIENT.put_item(
            TableName=os.environ['DYNAMODB_DETECTION_FILE_TABLE'],
            Item = {
                'repo':         {'S': os.environ['GITHUB_DETECTION_REPO']},
                'filename':     {'S': path},
                'commit_sha':   {'S': sha},
                'search':       {'S': search}
            }
        )
    except Exception as e:
        logger.error(f"ERROR: Unable to put file info in dynamondb -  {e}")


# Get a list of all the detection files in the repo.  Filter out non-detection files.
# Returns a list of dictionaries with this info:
#  "path": <path and filename>,
#  "mode": <number>,
#  "type": <blob|tree>,
#  "sha": <SHA>,
#  "size": <number>,
#  "url": "https://api.github.com/repos/<owner>/<repo>/git/blobs/<SHA>"
def get_list_of_detection_files(github_pat):
    file_list= []
    try:
        headers = {'Authorization': f'token {github_pat}'}
        response = requests.get(f"https://api.github.com/repos/{os.environ['GITHUB_DETECTION_REPO']}/git/trees/{os.environ['GITHUB_BASE_BRANCH']}?recursive=0", headers=headers )

        # Get all detection file's metadata and create a list
        tree_json = json.loads(response.content).get('tree', [])
        for file in tree_json:
            # Not sure if this needed since we could fitler out at some other place.
            if (file.get('type', '') == 'blob') and (file.get('path', '').endswith('.yml')):
                file_list.append(file)
    except Exception as e:
        logger.error(f"ERROR: Unable to get list of detection files -  {e}")
    return file_list


def lambda_handler(event, context):

    github_pat = get_github_pat()
    deployment_error = False

    ## Update Splunk with all the detections
    if event.get('get_all_detections', ''):
        logger.info(f"INFO: Getting all detections and deploying them to Splunk")
        file_list = get_list_of_detection_files(github_pat)
        for file in file_list:
            detection_file_json = get_detection_file_metadata(github_pat, file.get('url',''))
            detection_file = get_detection_file_contents(detection_file_json)
            #splunk_search = get_splunk_search(detection_file)
            # Change this so that when in 'preview-only' it doesn't return and error.
            if deploy_detection_to_splunk(file.get('path', ''), detection_file, event) and not event.get('preview_only', ''):
                update_file_tracker_item(detection_file_json.get('path', ''), detection_file_json.get('sha', ''), splunk_search)
            else:
                logger.error(f"ERROR: Unable to deploy detection to Splunk -  {detection_file_json.get('path', '')}")
                deployment_error = True
        if not deployment_error and not event.get('preview_only', ''):
            ### Get the current SHA and put it in the db
            #put_commit_sha_in_detection_repo_table(sha)
            pass
        else:
            logger.error(f"ERROR: Unable to deploy all detections to Splunk")
        return # Don't need to do the below if we're doing the above
    
    ## Check github for new or updated detections
    logger.info(f"INFO: Getting new and updated detections and deploying them to Splunk")
    # Get the SHA of the base branch
    current_sha = get_current_commit_sha_from_github(github_pat)
    # Get the last known SHA of the base branch from the database
    last_known_sha = get_last_commit_sha_from_db()

    # If no SHA found in db for the repo Put the current SHA in the db and deploy detections
    if not last_known_sha:
        put_commit_sha_in_detection_repo_table(current_sha)
    else:
        # Compare current SHA with last know SHA.  If SHA values are the same, then nothing to do
        if compare_sha_values(current_sha, last_known_sha) == 0:
            logger.info(f"INFO: No new or updated detections, so exiting process")
            return

    # If we've gotten to here, then we have new/updated detections
    ## Deploy Detections to Splunk
    # TODO: Send notification to messaging system saying we have new/updated files
    
    # Get new and updated detection info
    file_list = get_new_and_updated_detections_from_github(github_pat, current_sha, last_known_sha)
    
    # For file in the list of new/updated detections, deploy the detection to Splunk
    for file in file_list: 
        filename_and_path = ''
        file_status = file.get('status', '')

        file_response_json = get_detection_file_metadata(github_pat, file.get('contents_url', ''))
        detection_file = get_detection_file_contents(file_response_json)    
        splunk_search = get_splunk_search(detection_file)
        
        # Push new/updated detections to Splunk
        if file_status in ['added', 'modified']:
            if deploy_detection_to_splunk(file_response_json.get('path', ''), splunk_search, event):
                # If successful, then update the SHA in dynamodb
                update_file_tracker_item(file_response_json.get('path', ''), file_response_json.get('sha', ''), splunk_search)
            else:
                logger.error(f"ERROR: Unable to deploy detection to Splunk -  {file_response_json.get('path', '')}")
                deployment_error = True
        # Remove detections from Splunk
        elif file_status in ['renamed', 'removed']:
            remove_detection_from_splunk(filename_and_path) # not sure what info is needed to delete from Splunk
            remove_from_file_tracker()  
        else: 
            logger.info(f"INFO: Unknown status for detection file")
    if not deployment_error:
        put_commit_sha_in_detection_repo_table(current_sha)
    else:
        logger.error(f"ERROR: Unable to deploy all detections to Splunk")

    #TEST
    #headers = {'Authorization': f'token {github_pat}'}
    #response = requests.get('https://api.github.com/repos/misterjulien/detection_library_poc/compare/b901ca16ba553087e3bd9eadd44a9a9602172644...f6a23742a3521153ca69a128e94432eb125870e4', headers=headers )
    #print(f"response = {response.content}")

                
    # If not successful, send error message to Splunk?
    # Send notification that the process is complete

    # Future Idea - check Splunk search against detections in github
    # Future Idea - Periodically (once a day?) see if detections in Splunk match what's in github
    # Future Idea - Add playbook to yaml and push new/updated playbooks to Confluence






