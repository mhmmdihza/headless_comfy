from enum import Enum
import asyncpg
from typing import Optional, List, Dict

from urllib.parse import quote_plus

import urllib
from api.config import settings

pool: Optional[asyncpg.Pool] = None

class TaskStatus(Enum):
    IN_QUEUE = "IN_QUEUE"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    
async def init_db():
    user = settings.DB_USER
    password = settings.DB_PASSWORD
    host = settings.DB_HOST
    port = settings.DB_PORT
    database = settings.DB_SCHEMA

    encoded_password = quote_plus(password)
    conn_str = f"postgresql://{user}:{encoded_password}@{host}:{port}/{database}"
    global pool
    if not pool:
        pool = await asyncpg.create_pool(conn_str,
                                         statement_cache_size=0) #TODO currently using supabase free tier

# Function to insert a new queue record
async def insert_queue(s3_object_id: str, userid: str, prompt: str, image_input: str, status: TaskStatus = TaskStatus.IN_QUEUE):
    await pool.execute("""
        INSERT INTO queue (s3_object_id, userid, status, prompt, image_input)
        VALUES ($1, $2, $3, $4, $5)
    """, s3_object_id, userid, status.value, prompt, image_input)

# Function to update status and image_result by s3_object_id
async def update_status_result(s3_object_id: str, status: TaskStatus, image_result: Optional[str] = None):
    await pool.execute("""
        UPDATE queue
        SET status = $2,
            image_result = COALESCE($3, image_result),
            updated_on = now()
        WHERE s3_object_id = $1
    """, s3_object_id, status.value, image_result)

# Function to select all rows by userid
async def get_queues_by_user(userid: str) -> List[asyncpg.Record]:
    return await pool.fetch("""
        SELECT * FROM queue
        WHERE userid = $1
        ORDER BY created_on DESC
    """, userid)

# Function to select a single row by s3_object_id and userid
async def get_queue_by_id_and_user(s3_object_id: str, userid: str) -> Optional[asyncpg.Record]:
    return await pool.fetchrow("""
        SELECT * FROM queue
        WHERE s3_object_id = $1 AND userid = $2
    """, s3_object_id, userid)
