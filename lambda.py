import os
import boto3
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client('ec2')
sns = boto3.client('sns')

# Environment variables (configure in Lambda console)
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')  # required to send notifications
EXCLUDE_TAG_KEY = os.environ.get('EXCLUDE_TAG_KEY', 'Environment')
EXCLUDE_TAG_VALUES = [v.strip() for v in os.environ.get('EXCLUDE_TAG_VALUES', '').split(',') if v.strip()]


def should_exclude(instance):
    """Return True if instance should be excluded based on tags."""
    tags = instance.get('Tags', []) or []
    for t in tags:
        if t.get('Key') == EXCLUDE_TAG_KEY and t.get('Value') in EXCLUDE_TAG_VALUES:
            return True
    return False


def lambda_handler(event, context):
    try:
        # Find running instances
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

        # Publish to SNS if configured
        if SNS_TOPIC_ARN:
            try:
                sns.publish(TopicArn=SNS_TOPIC_ARN, Subject='EC2 Stop Notification', Message=message)
            except ClientError as e:
                logger.error(f"Failed to publish SNS message: {e}")

        return { 'status': 'ok', 'message': message }

    except Exception as e:
        logger.exception('Lambda execution failed')
        # Optionally publish an alarm to SNS
        if SNS_TOPIC_ARN:
            try:
                sns.publish(TopicArn=SNS_TOPIC_ARN, Subject='EC2 Stop Lambda Error', Message=str(e))
            except Exception:
                pass
        raise
