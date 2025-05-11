import requests
from api.config import settings

def runpod_status(id:str):
    headers = {
        "Authorization": settings.RUNPOD_SECRET
    }
    url = f"{settings.RUNPOD_URL}/status/{id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        status = data.get("status")
        message = data.get("output", {}).get("message") if status == "COMPLETED" else None
        return status, message
    else:
        raise ValueError(f"runpod status failed with status code {response.status_code}")