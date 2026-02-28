from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
from dotenv import load_dotenv

from app.routes import youtube
from app.routes.websocket import manager
from app.middleware.auth import AppIDMiddleware

# Load environment variables
load_dotenv()

# Get configuration from environment
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Create FastAPI app
app = FastAPI(
    title="YouTube Downloader API",
    description="Backend API for YouTube video downloading using yt-dlp",
    version="1.0.0",
)

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
