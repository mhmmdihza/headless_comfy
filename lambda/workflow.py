import base64
import json
import os
import uuid

import boto3
from log import logger

s3_client = boto3.client("s3")

# Load bucket name from environment variable
BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "satria-bucket")

def fetch_image_from_s3(bucket, key):
    try:
        logger.info(f"Fetching image from S3: bucket={bucket}, key={key}")
        response = s3_client.get_object(Bucket=bucket, Key=key)
        image_bytes = response["Body"].read()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        logger.info(f"Successfully fetched and encoded image: {key}")
        return image_base64
    except Exception as e:
        logger.error(f"Failed to fetch image from S3: {e}")
        raise
def load_image(image_key):
    try:
        return fetch_image_from_s3(BUCKET_NAME, image_key)
    except Exception as e:
        logger.error(f"Failed to load image from S3: {e}")
        raise

def build_request_body(message_data):
    workflow_name = message_data.get("workflow_name")
    try:
        match workflow_name:
            case None | "img2img_flux":
                return img2img_flux(message_data)
            case "workflow_a":
                return {"workflow": "A", "details": "Specific config for A"}
            case "workflow_b":
                return {"workflow": "B", "details": "Specific config for B"}
            case _:
                raise ValueError(f"Unknown workflow: {workflow_name}")
    except Exception as e:
        raise
        
def img2img_flux(message_data):
    #validate message_data
    image_key = message_data.get("image_key")
    prompt = message_data.get("prompt")
    if not prompt:
        logger.error(f"Missing prompt in message: {message_data}")
        raise ValueError("missing image_key or prompt")
    try:
        image_base64 = load_image(image_key)
    except Exception as e:
        raise

    unique_name = f"{uuid.uuid4().hex}.png"

    with open(os.path.join(os.path.dirname(__file__), "img2img_flux.json")) as f:
        workflow = json.load(f)

    workflow["15"]["inputs"]["clip_l"] = prompt
    workflow["15"]["inputs"]["t5xxl"] = prompt
    workflow["21"] = {"inputs": {"image": unique_name}, "class_type": "LoadImage", "_meta": {"title": "Load Image"}}

    body = {
        "input": {
            "images": [
                {
                    "name": unique_name,
                    "image": image_base64
                }
            ],
            "workflow": workflow
        }
    }
    return body