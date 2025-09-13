# 🚀 AWS Cost Optimization Project – Automatically Stop Unused EC2 Instances

## 📌 Project Overview
This project implements an **automated solution** to detect and stop unused/running EC2 instances on a schedule to save costs.  
It uses **AWS Lambda**, **EventBridge Scheduler**, **IAM**, **SNS**, and **CloudWatch Logs** to build a complete monitoring and automation flow.

---

## 🏗️ Architecture
EventBridge Scheduler (cron / rate)
│
▼
Lambda: StopUnusedEC2Instances
│
┌────────┴──────────┐
▼ ▼
EC2 API (stop) CloudWatch Logs
│
▼
SNS (Notifications)


---

## ✅ Prerequisites
- AWS account with access to:
  - Lambda
  - IAM roles & policies
  - EventBridge
  - EC2
  - SNS
- Keep all resources in the same AWS region for simplicity.
- AWS Console access (or AWS CLI configured).

---

## 🛠️ Services Used
- **AWS Lambda** – Python 3.11 function to stop EC2 instances.  
- **Amazon EventBridge (Scheduler)** – Triggers Lambda based on cron/rate.  
- **AWS IAM** – Permissions for Lambda to access EC2, SNS, and Logs.  
- **Amazon EC2** – Instances to be stopped.  
- **Amazon CloudWatch Logs** – Stores Lambda logs.  
- **Amazon SNS** – Sends email/SMS notifications when instances are stopped.  

---

## ⚙️ Implementation Steps
1. **Create IAM Role & Policies**
   - Attach `AWSLambdaBasicExecutionRole`
   - Create a custom inline policy for EC2 and SNS actions.

2. **Create SNS Topic & Subscription**
   - Topic name: `EC2StopNotifications`
   - Subscribe via Email/SMS.

3. **Create the Lambda Function**
   - Runtime: Python 3.11
   - Function name: `StopUnusedEC2Instances`
   - Attach execution role created earlier.
   - Add environment variables:
     - `SNS_TOPIC_ARN`
     - `EXCLUDE_TAG_KEY` (default: `Environment`)
     - `EXCLUDE_TAG_VALUES` (e.g., `Prod,DoNotStop`)

4. **Configure EventBridge Scheduler**
   - Test: run every minute → `cron(* * * * ? *)`
   - Production: hourly/daily cron expressions.

5. **Test End-to-End**
   - Start an EC2 instance.
   - Verify Lambda stops it.
   - Check SNS notifications.

---

## 🧩 Lambda Function (Python 3.11)

```python
import os
import boto3
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client('ec2')
sns = boto3.client('sns')

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
EXCLUDE_TAG_KEY = os.environ.get('EXCLUDE_TAG_KEY', 'Environment')
EXCLUDE_TAG_VALUES = [v.strip() for v in os.environ.get('EXCLUDE_TAG_VALUES', '').split(',') if v.strip()]

def should_exclude(instance):
    tags = instance.get('Tags', []) or []
    for t in tags:
        if t.get('Key') == EXCLUDE_TAG_KEY and t.get('Value') in EXCLUDE_TAG_VALUES:
            return True
    return False

def lambda_handler(event, context):
    try:
        resp = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
        instances_to_stop = []

        for reservation in resp.get('Reservations', []):
            for inst in reservation.get('Instances', []):
                instance_id = inst.get('InstanceId')
                if should_exclude(inst):
                    logger.info(f"Skipping {instance_id} due to tag exclusion")
                    continue
                instances_to_stop.append(instance_id)

        if instances_to_stop:
            logger.info(f"Stopping instances: {instances_to_stop}")
            ec2.stop_instances(InstanceIds=instances_to_stop)
            message = f"Stopped EC2 instances: {instances_to_stop}"
        else:
            message = "No eligible instances to stop."
            logger.info(message)

        if SNS_TOPIC_ARN:
            sns.publish(TopicArn=SNS_TOPIC_ARN, Subject='EC2 Stop Notification', Message=message)

        return { 'status': 'ok', 'message': message }

    except Exception as e:
        logger.exception('Lambda execution failed')
        if SNS_TOPIC_ARN:
            sns.publish(TopicArn=SNS_TOPIC_ARN, Subject='EC2 Stop Lambda Error', Message=str(e))
        raise
```

### 📊 Monitoring & Log Retention
Logs stored in CloudWatch Logs under /aws/lambda/StopUnusedEC2Instances

Set log retention to 7 or 30 days.

(Optional) Create CloudWatch Alarms for failures or abnormal stops.

### 🧹 Cleanup
Delete EventBridge Scheduler rule.

Delete Lambda function.

Delete IAM role/policies.

Delete SNS topic.

Stop/terminate test EC2 instances.

### ⏰ Cron Examples
Every minute (test): cron(* * * * ? *)

Hourly: rate(1 hour)

Daily at 9PM IST: cron(0 15 * * ? *)

### 📧 Notifications
SNS sends email/SMS alerts when:

Instances are stopped.

Lambda encounters an error.

### 🙌 Contribution
Feel free to fork, enhance, and raise PRs for improvements.


---







