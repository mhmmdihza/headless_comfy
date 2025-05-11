import json
import logging
from urllib.parse import urlparse
from api.db.postgres import TaskStatus, count_user_active_queues, get_queue_by_id_and_user, get_queues_by_user, insert_queue, update_status_result
from api.integration.runpod import RunpodException, runpod_status
from api.integration.s3 import get_image_froms3, upload_to_s3
from api.integration.sqs import send_message
from api.integration.webhook import generate_webhook_url

class ExceededLimit():
    pass

class NotExists():
    pass

logger = logging.getLogger(__name__)

async def new_queue(userid:str,image,prompt):
    countQueue = await count_user_active_queues(userid)
    if countQueue>0:
        raise ExceededLimit("Another request is still in the queue or in progress")
    try:
        keys = await upload_to_s3(image)
        key = keys[0]
        file_url = keys[1]
        
        webhook_url = generate_webhook_url(key)
        payload = {
            "image_key": key,
            "prompt": prompt,
            "webhook": webhook_url
        }
        await send_message(json.dumps(payload))

        await insert_queue(key,userid,prompt,file_url)
        return key
    except Exception as e:
        logger.error("new_queue Error: %s", str(e))
        raise e
    #except S3Exception as s3e:
    #    raise e

async def queues_by_user(userid):
    return await get_queues_by_user(userid)

async def update_status(id,status,image_result):
    await update_status_result(id,TaskStatus[status],image_result)

async def get_pending_queue(id,userid):
    queue = await get_queue_by_id_and_user(id,userid)
    if not queue:
        return None
    if TaskStatus[queue.get("status")] in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
        return None
    return queue
    
        
async def get_latest_status(id,userid):
    try:
        queue = await get_queue_by_id_and_user(id,userid)
        if not queue:
            raise NotExists("Not Found")
        
        status = TaskStatus[queue["status"]]
        image_result = queue.get("image_result")
        latestStatus = None        
        if status == TaskStatus.IN_PROGRESS or status == TaskStatus.IN_QUEUE:
            runpodStatus, result_url = await runpod_status(queue["runpod_id"])
            latestStatus = TaskStatus[runpodStatus]
            if status != latestStatus:
                await update_status_result(id,latestStatus,result_url)
            if latestStatus == TaskStatus.COMPLETED:
                image_result = result_url
        else:
            latestStatus = status
        
        if latestStatus ==  TaskStatus.COMPLETED:
            file_stream = await get_image(image_result)
            return latestStatus.value,file_stream
        else:
            return latestStatus.value , None
    except RunpodException as re:
        logger.error("Runpod status: %s", str(re))
        await update_status_result(id,TaskStatus.FAILED)
        raise re
    except Exception as e:
        logger.error("get_latest_status : %s", str(e))
        raise e

async def get_image(image_result):
    parsed_url = urlparse(image_result)
    object_key = parsed_url.path.lstrip('/')
    return await get_image_froms3(object_key)