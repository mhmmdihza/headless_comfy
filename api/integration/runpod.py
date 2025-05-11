import aiohttp
import asyncio
from api.config import settings

class RunpodException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)

async def runpod_status(id: str):
    headers = {
        "Authorization": settings.RUNPOD_SECRET
    }
    url = f"{settings.RUNPOD_URL}/status/{id}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json() 
                status = data.get("status")
                message = data.get("output", {}).get("message") if status == "COMPLETED" else None
                return status, message
            elif response.status == 404:
                raise RunpodException(404, "record not found or has already expired")
            else:
                raise ValueError(f"runpod status failed with status code {response.status}")
