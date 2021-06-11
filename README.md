# MACS-Verify

Custom Discord bot used to verify students and staff on the MACS Discord server 

## Requirements
* Discord members intent enabled
* Amazon Simple Email Service (SES) API to be configured with Access Key

## Usage
1. Place AWS [credential and config](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#configuration) file in `discord_verify/aws/crentials` and `discord_verify/aws/config`
2. Edit `discord_verify/discord_secrets.ini` and add your discord bot token
```
[DEFAULT]
discord_token = <DISCORD_BOT_TOKEN>
```
3. `docker-compose up -d`


## Quickstart with Terraform
```
cd terraform && terraform apply
aws ec2-instance-connect send-ssh-public-key --instance-id=<INSTANCE_ID> --instance-os-user=ec2-user --ssh-public-key="$(cat ~/.ssh/id_rsa.pub)" --availability-zone=<AVAILABILITY_ZONE>
ssh ec2-user@<INSTANCE_DNS>
```
Then configure as specified in Usage and set `aws_instance = True` in `discord_verify/config.ini`