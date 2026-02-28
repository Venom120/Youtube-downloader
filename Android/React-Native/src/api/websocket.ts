import { WS_URL, WS_EVENTS, APP_ID } from "./config";

export type DownloadProgressData = {
  downloadId: string;
  videoId: string;
  progress: number; // 0-100
  downloadedBytes: number;
  totalBytes: number;
  speed: string; // e.g., "1.2 MB/s"
  eta: string; // e.g., "00:05"
};

export type DownloadCompleteData = {
  downloadId: string;
  videoId: string;
  filePath: string;
  fileName: string;
};

export type DownloadErrorData = {
  downloadId: string;
  videoId: string;
  error: string;
};

type EventCallback = (data: any) => void;

/**
 * WebSocket client for real-time download progress updates
 */
class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000; // 3 seconds
  private reconnectTimer: NodeJS.Timeout | null = null;
  private eventHandlers: Map<string, Set<EventCallback>> = new Map();
  private isIntentionalClose = false;
  private subscribedDownloads: Set<string> = new Set();

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log("[WebSocket] Already connected");
      return;
    }

    try {
      console.log("[WebSocket] Connecting to:", WS_URL);
      this.isIntentionalClose = false;
      
      // Include app ID in WebSocket connection URL
      this.ws = new WebSocket(`${WS_URL}/ws?app_id=${APP_ID}`);

      this.ws.onopen = () => {
        console.log("[WebSocket] Connected successfully");
        this.reconnectAttempts = 0;
        this.emit(WS_EVENTS.CONNECT, {});
        
        // Re-subscribe to all downloads after reconnection
        this.subscribedDownloads.forEach((downloadId) => {
          this.subscribeToDownload(downloadId);
        });
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log("[WebSocket] Message received:", message.type);
          
          if (message.type && message.data) {
            this.emit(message.type, message.data);
          }
        } catch (error) {
          console.error("[WebSocket] Failed to parse message:", error);
        }
      };

      this.ws.onerror = (error) => {
        console.error("[WebSocket] Error:", error);
      };

      this.ws.onclose = (event) => {
        console.log("[WebSocket] Disconnected:", event.code, event.reason);
        this.emit(WS_EVENTS.DISCONNECT, { code: event.code, reason: event.reason });
        this.ws = null;

        // Attempt to reconnect unless it was intentional
        if (!this.isIntentionalClose && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };
    } catch (error) {
      console.error("[WebSocket] Connection failed:", error);
      this.scheduleReconnect();
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * this.reconnectAttempts;
    
    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.isIntentionalClose = true;
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close(1000, "Client disconnect");
      this.ws = null;
    }
    
    this.subscribedDownloads.clear();
  }

  /**
   * Send message to server
   */
  private send(type: string, data: any): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn("[WebSocket] Cannot send message - not connected");
      return;
    }

    try {
      const message = JSON.stringify({ type, data });
      this.ws.send(message);
      console.log("[WebSocket] Sent:", type);
    } catch (error) {
      console.error("[WebSocket] Failed to send message:", error);
    }
  }

  /**
   * Subscribe to download progress updates
   */
  subscribeToDownload(downloadId: string): void {
    this.subscribedDownloads.add(downloadId);
    this.send(WS_EVENTS.SUBSCRIBE, { downloadId });
  }

  /**
   * Unsubscribe from download progress updates
   */
  unsubscribeFromDownload(downloadId: string): void {
    this.subscribedDownloads.delete(downloadId);
    this.send(WS_EVENTS.UNSUBSCRIBE, { downloadId });
  }

  /**
   * Request download resume
   */
  resumeDownload(downloadId: string): void {
    this.send(WS_EVENTS.RESUME_DOWNLOAD, { downloadId });
  }

  /**
   * Request download cancellation
   */
  cancelDownload(downloadId: string): void {
    this.send(WS_EVENTS.CANCEL_DOWNLOAD, { downloadId });
  }

  /**
   * Register event handler
   */
  on(event: string, callback: EventCallback): void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    this.eventHandlers.get(event)!.add(callback);
  }

  /**
   * Unregister event handler
   */
  off(event: string, callback: EventCallback): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.delete(callback);
    }
  }

  /**
   * Emit event to all registered handlers
   */
  private emit(event: string, data: any): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach((callback) => {
        try {
          callback(data);
        } catch (error) {
          console.error(`[WebSocket] Error in event handler for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// Export singleton instance
export const wsClient = new WebSocketClient();
export default wsClient;
