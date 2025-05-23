import asyncio
import boto3
from api.config import settings

queue_url = settings.SQS_URL

async def send_message(message):
    try:
        sqs = boto3.client('sqs', region_name=settings.SQS_REGION)
        await asyncio.to_thread(sqs.send_message, QueueUrl=queue_url, MessageBody=message)
    except Exception as e:
        raise