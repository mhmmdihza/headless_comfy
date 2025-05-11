from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()  # Load .env file into environment variables

class Settings(BaseSettings):
    JWT_SECRET: str
    CORS_ORIGINS: List[str]
    S3_REGION:str
    S3_BUCKET_NAME:str
    DB_HOST:str
    DB_PORT:str
    DB_SCHEMA:str
    DB_USER:str
    DB_PASSWORD:str
    SQS_REGION:str
    SQS_URL:str
    RUNPOD_URL:str
    RUNPOD_SECRET:str

    class Config:
        env_file = ".env"

settings = Settings()
