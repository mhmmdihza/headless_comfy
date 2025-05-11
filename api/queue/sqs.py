import boto3
from api.config import settings

queue_url = settings.SQS_URL

def send_message(message):
    try:
        sqs = boto3.client('sqs', region_name=settings.SQS_REGION)
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=message
        )
        print("Message ID:", response['MessageId'])
    except Exception as e:
        raise