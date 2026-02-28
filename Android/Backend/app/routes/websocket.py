from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Optional, Set
import json
import asyncio

from middleware.auth import validate_app_id_ws


class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting
    """

    def __init__(self):
        # Map of download_id -> set of connected websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Map of websocket -> set of subscribed download_ids
        self.subscriptions: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket, app_id: Optional[str] = None):
        """Accept WebSocket connection"""
        # Validate app ID
        if not app_id or not validate_app_id_ws(app_id):
            await websocket.close(code=4003, reason="Invalid App ID")
            return

        await websocket.accept()
        self.subscriptions[websocket] = set()
        print(f"[WebSocket] Client connected")

        try:
            await self.handle_messages(websocket)
        except WebSocketDisconnect:
            self.disconnect(websocket)
            print(f"[WebSocket] Client disconnected")

    def disconnect(self, websocket: WebSocket):
        """Remove websocket connection"""
        # Remove from all subscriptions
        if websocket in self.subscriptions:
            download_ids = self.subscriptions[websocket]
            for download_id in download_ids:
                if download_id in self.active_connections:
                    self.active_connections[download_id].discard(websocket)
                    if not self.active_connections[download_id]:
                        del self.active_connections[download_id]
            del self.subscriptions[websocket]

    async def handle_messages(self, websocket: WebSocket):
        """Handle incoming WebSocket messages"""
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                msg_type = message.get("type")
                msg_data = message.get("data", {})

                if msg_type == "subscribe":
                    await self.subscribe(websocket, msg_data.get("downloadId"))
                elif msg_type == "unsubscribe":
                    await self.unsubscribe(websocket, msg_data.get("downloadId"))
                elif msg_type == "resume_download":
                    await self.handle_resume(websocket, msg_data.get("downloadId"))
                elif msg_type == "cancel_download":
                    await self.handle_cancel(websocket, msg_data.get("downloadId"))
                else:
                    print(f"[WebSocket] Unknown message type: {msg_type}")

            except WebSocketDisconnect:
                raise
            except Exception as e:
                print(f"[WebSocket] Error handling message: {e}")

    async def subscribe(self, websocket: WebSocket, download_id: str):
        """Subscribe websocket to download progress updates"""
        if not download_id:
            return

        print(f"[WebSocket] Client subscribed to download: {download_id}")

        # Add to active connections for this download
        if download_id not in self.active_connections:
            self.active_connections[download_id] = set()
        self.active_connections[download_id].add(websocket)

        # Track subscription
        if websocket in self.subscriptions:
            self.subscriptions[websocket].add(download_id)

    async def unsubscribe(self, websocket: WebSocket, download_id: str):
        """Unsubscribe websocket from download progress updates"""
        if not download_id:
            return

        print(f"[WebSocket] Client unsubscribed from download: {download_id}")

        # Remove from active connections
        if download_id in self.active_connections:
            self.active_connections[download_id].discard(websocket)
            if not self.active_connections[download_id]:
                del self.active_connections[download_id]

        # Remove from subscriptions
        if websocket in self.subscriptions:
            self.subscriptions[websocket].discard(download_id)

    async def handle_resume(self, websocket: WebSocket, download_id: str):
        """Handle resume download request"""
        print(f"[WebSocket] Resume request for download: {download_id}")
        # Implementation depends on ytdlp_service capabilities
        # For now, just acknowledge
        await self.send_message(
            websocket,
            {
                "type": "download_resumed",
                "data": {"downloadId": download_id},
            },
        )

    async def handle_cancel(self, websocket: WebSocket, download_id: str):
        """Handle cancel download request"""
        from services.ytdlp_service import ytdlp_service

        print(f"[WebSocket] Cancel request for download: {download_id}")
        
        success = ytdlp_service.cancel_download(download_id)
        
        if success:
            await self.broadcast_to_download(
                download_id,
                {
                    "type": "download_cancelled",
                    "data": {"downloadId": download_id},
                },
            )

    async def send_message(self, websocket: WebSocket, message: dict):
        """Send message to specific websocket"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"[WebSocket] Error sending message: {e}")

    async def broadcast_to_download(self, download_id: str, message: dict):
        """Broadcast message to all clients subscribed to a download"""
        if download_id not in self.active_connections:
            return

        disconnected = set()
        for websocket in self.active_connections[download_id]:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                print(f"[WebSocket] Error broadcasting: {e}")
                disconnected.add(websocket)

        # Remove disconnected websockets
        for websocket in disconnected:
            self.disconnect(websocket)

    async def send_progress(self, download_id: str, progress_data: dict):
        """Send download progress update"""
        await self.broadcast_to_download(
            download_id,
            {
                "type": "download_progress",
                "data": progress_data,
            },
        )

    async def send_complete(self, download_id: str, complete_data: dict):
        """Send download completion notification"""
        await self.broadcast_to_download(
            download_id,
            {
                "type": "download_complete",
                "data": complete_data,
            },
        )

    async def send_error(self, download_id: str, error_data: dict):
        """Send download error notification"""
        await self.broadcast_to_download(
            download_id,
            {
                "type": "download_error",
                "data": error_data,
            },
        )


# Singleton manager instance
manager = ConnectionManager()
