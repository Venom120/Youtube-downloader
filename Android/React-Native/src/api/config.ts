import { BACKEND_URL as ENV_BACKEND_URL, WS_URL as ENV_WS_URL, APP_ID as ENV_APP_ID } from '@env';

/**
 * Backend API Configuration
 * Values are loaded from .env file
 */

// Backend server URL - Loaded from .env
export const BACKEND_URL = ENV_BACKEND_URL || "http://localhost:8000";
export const WS_URL = ENV_WS_URL || "ws://localhost:8000";

// App identifier for backend authentication - Loaded from .env
export const APP_ID = ENV_APP_ID || "com.venom120.ytdownloader";

// API endpoints
export const API_ENDPOINTS = {
  SEARCH: "/api/search",
  VIDEO_INFO: "/api/video-info",
  DOWNLOAD: "/api/download",
  DOWNLOAD_STATUS: "/api/download-status",
  CANCEL_DOWNLOAD: "/api/cancel-download",
};

// WebSocket events
export const WS_EVENTS = {
  CONNECT: "connect",
  DISCONNECT: "disconnect",
  DOWNLOAD_PROGRESS: "download_progress",
  DOWNLOAD_COMPLETE: "download_complete",
  DOWNLOAD_ERROR: "download_error",
  DOWNLOAD_CANCELLED: "download_cancelled",
  SUBSCRIBE: "subscribe",
  UNSUBSCRIBE: "unsubscribe",
  RESUME_DOWNLOAD: "resume_download",
  CANCEL_DOWNLOAD: "cancel_download",
};
