from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from jose import jwt

class JWTAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret: str):
        super().__init__(app)
        self.secret = secret

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path.startswith("/auth/"):
            return await call_next(request)
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing Authorization header")

        token = auth_header[7:]  # Remove "Bearer "
        try:
            payload = jwt.decode(token, self.secret, algorithms=["HS256"],audience="authenticated")  # Supabase uses HS256 by default
            request.state.user_id = payload.get("sub")
        except Exception as e:
            print(f"JWT decoding error: {e}")
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})

        return await call_next(request)
