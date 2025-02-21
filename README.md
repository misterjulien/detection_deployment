# detection_deployment
This is a basic detection deployment automation.  It stores detections in github and 
automatically deploys them when detections are added or updated.

<p align="center">
<img src=https://github.com/user-attachments/assets/dc6832a3-3304-4a82-a57c-6b55c091d4bc>
</p>


## Process
1. Lambda is scheduled to run periodically.
2. Compare the current github repo hash with the repo hash stored in db.
3. If the hashes are different, get the new/updated files from previous commits.
4. Deploy the new/updated detections to the SIEM.
5. Update the db with the current hash.

## Deploy All Detections
To update the detection database and deploy all detections, delete the 'Repo'
from the 'detection_repo_tracker' and run the Lambda function.

## TODO
The code to deploy to Splunk is not complete, so you'll need to update that if you're 
deploying to your own Splunk instance.  It's possible to deploy to multiple security tools 
with the addition of some logic.
