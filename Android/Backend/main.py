from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
from dotenv import load_dotenv

from routes import youtube
from routes.websocket import manager
from middleware.auth import AppIDMiddleware

# Load environment variables
load_dotenv()

# Get configuration from environment
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute", "2000/hour"])

# Create FastAPI app
app = FastAPI(
    title="YouTube Downloader API",
    description="Backend API for YouTube video downloading using yt-dlp",
    version="1.0.0",
)

# Add rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Normalize HTTPException payload to { error: "..." }
    detail = exc.detail if hasattr(exc, "detail") else str(exc)
    return JSONResponse(status_code=exc.status_code, content={"error": detail})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log and return a simple JSON error message
    print(f"[ERROR] Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"error": "Internal server error"})

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Loaded from environment variable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add App ID authentication middleware
app.add_middleware(AppIDMiddleware)

# Include routers
app.include_router(youtube.router, prefix="/api", tags=["YouTube"])

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, app_id: Optional[str] = None):
    if not app_id:
        await websocket.close(code=1008, reason="App ID is required")
        return
    await manager.connect(websocket, app_id)


@app.get("/api")
async def root():
    return {
        "message": "YouTube Downloader API",
        "status": "running",
        "version": "2.0.0",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
