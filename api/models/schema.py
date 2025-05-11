from pydantic import BaseModel
from typing import Optional

class GenerationRequest(BaseModel):
    prompt: str
    resolution: Optional[str] = "512x512"
    seed: Optional[int] = None

class GenerationResponse(BaseModel):
    job_id: str

class JobStatusResponse(BaseModel):
    status: str
    result_url: Optional[str] = None

class QueueItemResponse(BaseModel):
    s3_object_id: str
    status: str
    created_on: str
