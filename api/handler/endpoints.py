import asyncio
import json
import logging
from typing import Dict, List
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, Response, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from api.integration.runpod import RunpodException
from api.middleware.jwt import decode_jwt_token
from api.integration.webhook import verify_signature
from api.models.schema import GenerationResponse, JobStatusResponse, QueueItemResponse
from api.services.queue import ExceededLimit, get_latest_status, get_pending_queue, new_queue, queues_by_user, update_status

router = APIRouter()

logger = logging.getLogger(__name__)

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_IMAGE_TYPES = ["image/jpeg","image/jpg","image/png"]

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
        key = await new_queue(request.state.user_id,image,prompt)
        return GenerationResponse(job_id=key)
    except ExceededLimit as el:
        raise HTTPException(status_code=400, detail="Another request is still in the queue or in progress")
    except Exception as e :
        logger.error("Error Generate: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Internal error")

@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_status(
    request: Request,
    job_id: str):
    try:
        status, file_stream = await get_latest_status(job_id,request.state.user_id)
        headers = {
            "X-Image-Metadata": json.dumps({"status": status}),
            "Cache-Control": "no-store"
        }
        if file_stream is not None:
            headers["Cache-Control"] = "public, max-age=86400"
            return StreamingResponse(file_stream, media_type="image/png", headers=headers)
        return Response(status_code=200, headers=headers)                 
    except RunpodException as re:
        raise HTTPException(status_code=re.code,detail=re.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal error")
    
@router.get("/queues", response_model=List[QueueItemResponse])
async def get_queues(request: Request):
    rows = await queues_by_user(request.state.user_id )
    formatted_rows = []
    for row in rows:
        formatted_row = QueueItemResponse(
            s3_object_id=row['s3_object_id'],
            status=row['status'],
            created_on=row['created_on'].strftime('%Y-%m-%d %H:%M')  # Format timestamp
        )
        formatted_rows.append(formatted_row)
    
    return formatted_rows
    

@router.post("/webhook/{id}")
async def webhook(id: str, request: Request, background_tasks: BackgroundTasks):
    sig = request.query_params.get("sig")
    if not sig:
        raise HTTPException(status_code=400, detail="Missing signature")

    if not verify_signature(id, sig):
        raise HTTPException(status_code=403, detail="Invalid signature")

    data = await request.json()
    status = data.get("status")
    result_url = data.get("output", {}).get("message")
    await update_status(id,status,result_url)
    background_tasks.add_task(send_message_to_user, id, status)

    return Response(status_code=200)

user_connections: Dict[str, List[WebSocket]] = {}
user_connections_lock = asyncio.Lock()


async def send_message_to_user(id: str, message: str):
    connections = user_connections.get(id, [])
    
    for connection in connections:
        try:
            await connection.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message for id {id}: {e}")

@router.websocket("/ws/status")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...),id: str = Query(...)):
    try:
        payload = decode_jwt_token(token)
        userid = payload.get("sub")
        queue = await get_pending_queue(id,userid)
        if not queue:
            await websocket.close(code=1008)
            return

    except Exception as e:
        logger.error("websocket error: %s", {e})
        await websocket.close(code=1008)
        return
    
    await websocket.accept()
    async with user_connections_lock:
        if id not in user_connections:
            user_connections[id] = []

        user_connections[id].append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(data)
            if data == "COMPLETED":
                break
        
        await websocket.close()
    except WebSocketDisconnect:
        async with user_connections_lock:
            if id in user_connections:
                user_connections[id].remove(websocket)
                
                if not user_connections[id]:
                    del user_connections[id]
        logger.debug("Client disconnected")