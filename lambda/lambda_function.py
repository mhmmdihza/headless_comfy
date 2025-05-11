import json
import boto3
import urllib3
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from workflow import build_request_body
from log import logger

# Clients
secrets_client = boto3.client("secretsmanager")
s3_client = boto3.client("s3")
http = urllib3.PoolManager()

# Load bucket name from environment variable
BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "satria-bucket")

def get_secrets(secret_name, region_name="us-east-1"):
    response = secrets_client.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])

def extract_message(event):
    if "Records" in event:
        return event["Records"][0].get("body")
    logger.error("No 'Records' found in the event")
    return None

def parse_message(message):
    try:
        return json.loads(message)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON message: {e}")
        return None

def load_secrets():
    try:
        runpod_secrets = get_secrets("runpod")
        postgres_secrets = get_secrets("postgres")
        logger.info("Secrets loaded successfully")
        return {
            "runpod": runpod_secrets,
            "postgres": postgres_secrets
        }
    except Exception as e:
        logger.error(f"Failed to load secrets: {e}")
        raise

def send_post_request_runpod(url, token, payload):
    try:
        logger.info("Making POST request to the API")
        response = http.request(
            "POST",
            url,
            body=json.dumps(payload),
            headers={
                "Content-Type": "application/json",
                "Authorization": token
            }
        )
        logger.info(f"Response status: {response.status}")

        response_json = json.loads(response.data.decode("utf-8"))
        status = response_json.get("status", "ERROR")
        runpod_id = response_json.get("id")

        return response, status, runpod_id

    except Exception as e:
        logger.error(f"Error during POST request: {e}")
        raise

def send_post_request_webhook(url, status):
    payload = {
        "status": status
    }
    try:
        logger.info("Making POST request to the webhook")
        response = http.request(
            "POST",
            url,
            body=json.dumps(payload),
            headers={
                "Content-Type": "application/json"
            }
        )
        logger.info(f"webhook Response status: {response.status}")
    except Exception as e:
        logger.error(f"Error during POST webhook: {e}")
    

def update_queue_status(db_config, s3_object_id, status,runpod_id=None, image_result=None):
    query = """
        UPDATE queue
        SET status = %s,
            runpod_id = COALESCE(%s, runpod_id),
            image_result = COALESCE(%s, image_result),
            updated_on = now()
        WHERE s3_object_id = %s
    """
    try:
        conn = psycopg2.connect(
            user=db_config["DB_USER"],
            password=db_config["DB_PASSWORD"],
            host=db_config["DB_HOST"],
            port=db_config["DB_PORT"],
            database=db_config["DB_SCHEMA"],
            connect_timeout=5
        )
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, (status, runpod_id, image_result, s3_object_id))
                logger.info(f"Updated DB for {s3_object_id} with status {status}")
    except Exception as e:
        logger.error(f"Database update failed: {e}")
        raise
    finally:
        if conn:
            conn.close()

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    status_to_update = "ERROR"
    image_key = None  # Define early for use in `finally`

    try:
        message = extract_message(event)
        if not message:
            return {"statusCode": 400, "body": "No 'Records' found in the event"}

        message_data = parse_message(message)
        if not message_data:
            return {"statusCode": 400, "body": "Invalid message format"}

        #image_key are mandatory , for id of request
        image_key = message_data.get("image_key")
        if not image_key:
            return {"statusCode": 400, "body": "Missing image_key"}

        try:
            payload = build_request_body(message_data)
        except Exception as e:
            try:
                update_queue_status(
                    db_config=load_secrets()["postgres"],
                    s3_object_id=image_key,
                    status="FAILED",
                )
            except Exception as db_err:
                logger.error(f"Status update failed after load_image error: {db_err}")
            return {"statusCode": 500, "body": str(e)}
    
        secrets = load_secrets()
        url = secrets["runpod"]["api_url"]
        token = secrets["runpod"]["api_token"]
        db_config = secrets["postgres"]


        response, status_to_update, runpod_id = send_post_request_runpod(
            url, token, payload
        )
        body = response.data.decode("utf-8")
        try:
            update_queue_status(
                db_config=db_config,
                s3_object_id=image_key,
                status=status_to_update,
                runpod_id=runpod_id,
            )
            webhook_url = message_data.get("webhook")
            if webhook_url:
                send_post_request_webhook(webhook_url,status_to_update)
        except Exception as db_err:
            logger.error(f"Final status update failed: {db_err}")
        return {
            "statusCode": response.status,
            "body": body
        }

    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        return {"statusCode": 500, "body": str(e)}
            
