import asyncio
import base64
import boto3
import uuid
from api.config import settings

class S3Exception:
    pass

def __init_s3_client():
    region = settings.S3_REGION
    return boto3.client('s3', region_name=region)

def get_image_froms3_sync(object_key):
    bucket = settings.S3_BUCKET_NAME
    s3 = __init_s3_client()
    try:
        response = s3.get_object(Bucket=bucket, Key=object_key)
        return response['Body']
    except Exception as e:
        raise e
    
async def get_image_froms3(object_key):
    try:
        return await asyncio.to_thread(get_image_froms3_sync,object_key)
    except Exception as e:
        raise S3Exception("failed to get image") from e
    
def upload_to_s3_sync(image):
    key = str(uuid.uuid4())
    bucket = settings.S3_BUCKET_NAME
    region = settings.S3_REGION

    s3_client = __init_s3_client()
    file_url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"

    try:
        s3_client.upload_fileobj(image.file, settings.S3_BUCKET_NAME, key)
    except Exception as e:
        raise e
    return [key,file_url]

async def upload_to_s3(image):
    try:
        return await asyncio.to_thread(upload_to_s3_sync, image)
    except Exception as e:
        raise S3Exception("failed to upload") from e