from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

ALLOWED_APP_ID = os.getenv("ALLOWED_APP_ID", "com.venom120.ytdownloader")


class AppIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate App ID from request headers
    Only requests with valid X-App-ID header are allowed
    """

    async def dispatch(self, request: Request, call_next):
        # Skip authentication for root and health check endpoints
        if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Check for App ID in headers
        app_id = request.headers.get("X-App-ID")

        if not app_id:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Missing X-App-ID header"},
            )

        if app_id != ALLOWED_APP_ID:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Invalid App ID"},
            )

        # App ID is valid, proceed with request
        response = await call_next(request)
        return response


def validate_app_id_ws(app_id: str) -> bool:
    """
    Validate App ID for WebSocket connections
    """
    return app_id == ALLOWED_APP_ID
