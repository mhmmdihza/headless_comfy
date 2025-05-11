import json
from typing import List
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException, Request, Response, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from api.integration.runpod import runpod_status
from api.queue.s3 import get_image_froms3, upload_to_s3
from api.models.schema import GenerationResponse, JobStatusResponse, QueueItemResponse
from api.db.postgres import TaskStatus, get_queue_by_id_and_user, get_queues_by_user, insert_queue, update_status_result
from api.queue.sqs import send_message

router = APIRouter()


MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_IMAGE_TYPES = ["image/jpeg","image/png"]

@router.post("/generate", response_model=GenerationResponse)
async def generate(
    request: Request,
    image: UploadFile = File(...),
    prompt: str = Form(...)
):
    contents = await image.read()

    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Image size must be less than 5MB"
        )

    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )
    image.file.seek(0)

    try:
        keys = upload_to_s3(image)
        key = keys[0]
        file_url = keys[1]

        payload = {
            "image_key": key,
            "prompt": prompt
        }
        send_message(json.dumps(payload))

        await insert_queue(key,request.state.user_id,prompt,file_url)
    except Exception as e :
        print(f"Error Generate: {e}")
        raise HTTPException(status_code=500, detail="Internal error")
    return GenerationResponse(job_id=key)

@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_status(
    request: Request,
    job_id: str):
    try:
        queue = await get_queue_by_id_and_user(job_id,request.state.user_id)
        if not queue:
            raise HTTPException(status_code=404, detail="Not Found")
        
        status = TaskStatus[queue["status"]]
        headers = {
            "X-Image-Metadata": json.dumps({"status": status.value})
        }
        def get_image_from_queue():
            image_result = queue["image_result"]
            parsed_url = urlparse(image_result)
            object_key = parsed_url.path.lstrip('/')
            return get_image_froms3(object_key)
        if status == TaskStatus.COMPLETED:
            file_stream = get_image_from_queue()
            
            headers["Cache-Control"] = "public, max-age=86400"
            return StreamingResponse(file_stream, media_type="image/png", headers=headers)
        elif status == TaskStatus.IN_PROGRESS:
            runpodStatus, result_url = runpod_status(queue["runpod_id"])
            latestStatus = TaskStatus[runpodStatus]
            if status != latestStatus:
                await update_status_result(job_id,latestStatus,result_url)
            if latestStatus ==  TaskStatus.COMPLETED:
                file_stream = get_image_from_queue()
                headers["Cache-Control"] = "public, max-age=86400"
                return StreamingResponse(file_stream, media_type="image/png", headers=headers)
            else:
                return Response(status_code=200, headers=headers)                 
        elif status == TaskStatus.FAILED:
            return Response(status_code=200, headers=headers)
        else:
            return Response(status_code=200, headers=headers)
    except Exception as e:
        print(f"Error get status: {e}")
        raise HTTPException(status_code=500, detail="Internal error")
    
@router.get("/queues", response_model=List[QueueItemResponse])
async def get_queues(request: Request):
    rows = await get_queues_by_user(request.state.user_id )
    formatted_rows = []
    for row in rows:
        formatted_row = QueueItemResponse(
            s3_object_id=row['s3_object_id'],
            status=row['status'],
            created_on=row['created_on'].strftime('%Y-%m-%d %H:%M')  # Format timestamp
        )
        formatted_rows.append(formatted_row)
    
    return formatted_rows
    

