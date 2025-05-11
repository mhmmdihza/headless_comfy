import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from jose import jwt
from api.config import settings

logger = logging.getLogger(__name__)

class JWTAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        if (request.method == "OPTIONS"
            or request.url.path.startswith("/auth/")
            or request.url.path.startswith("/webhook/")
        ):
            return await call_next(request)
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Invalid or missing Authorization header"})

        token = auth_header[7:]  # Remove "Bearer "
        try:
            payload = decode_jwt_token(token)
            request.state.user_id = payload.get("sub")
        except Exception as e:
            logger.error("JWT decoding error: %s", e)
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})

        return await call_next(request)
    
def decode_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET , algorithms=["HS256"],audience="authenticated")
        return payload
    except Exception as e:
        logger.error("JWT decoding error: %s", e)
        raise
