import * as FileSystem from "expo-file-system/legacy";
import AsyncStorage from "@react-native-async-storage/async-storage";
import RNBackgroundDownloader from "@kesha-antonov/react-native-background-downloader";
import { VideoInfo, SearchResult } from "../models/videoModel";
import {
  YouTubeAPI,
  wsClient,
  WS_EVENTS,
  DownloadProgressData,
  DownloadCompleteData,
  DownloadErrorData,
} from "../api";

const STORAGE_KEY_DOWNLOADS = "@ytdownloader_active_downloads";

type BackgroundDownloadTask = {
  id: string;
  url: string;
  destination: string;
  task?: any; // RNBackgroundDownloader task
};

export class YTDLPWrapper {
  private cachePath: string;
  private finalDownloadPath: string;
  private finalIsSaf: boolean;
  public readonly libName = "Backend Server (yt-dlp) + WebSocket";

  // Track active background downloads
  private backgroundDownloads: Map<string, BackgroundDownloadTask> = new Map();
  
  // Track download progress callbacks
  private progressCallbacks: Map<string, (progress: number) => void> = new Map();
  private completeCallbacks: Map<string, (filename: string) => void> = new Map();
  private errorCallbacks: Map<string, (error: string) => void> = new Map();
  
  private isWebSocketConnected: boolean = false;

  constructor(cachePath?: string, finalDownloadPath?: string, finalIsSaf: boolean = false) {
    this.cachePath = this.normalizeDirUri(cachePath);
    this.finalDownloadPath = finalDownloadPath || "";
    this.finalIsSaf = !!finalIsSaf;

    // Initialize WebSocket connection
    this.initializeWebSocket();
    
    // Restore active downloads on initialization
    this.restoreActiveDownloads();
  }

  private normalizeDirUri(path?: string): string {
    if (!path || typeof path !== "string") {
      return "";
    }
    return path.endsWith("/") ? path : `${path}/`;
  }

  /**
   * Initialize WebSocket connection and event handlers
   */
  private initializeWebSocket(): void {
    console.log("[Wrapper] Initializing WebSocket connection");
    
    // Connect to WebSocket
    wsClient.connect();

    // Handle connection events
    wsClient.on(WS_EVENTS.CONNECT, () => {
      console.log("[Wrapper] WebSocket connected");
      this.isWebSocketConnected = true;
      
      // Re-subscribe to all active downloads
      this.backgroundDownloads.forEach((download) => {
        wsClient.subscribeToDownload(download.id);
      });
    });

    wsClient.on(WS_EVENTS.DISCONNECT, () => {
      console.log("[Wrapper] WebSocket disconnected");
      this.isWebSocketConnected = false;
    });

    // Handle download progress updates
    wsClient.on(WS_EVENTS.DOWNLOAD_PROGRESS, (data: DownloadProgressData) => {
      console.log(`[Wrapper] Progress update for ${data.downloadId}: ${data.progress}%`);
      
      const callback = this.progressCallbacks.get(data.downloadId);
      if (callback) {
        callback(data.progress);
      }
    });

    // Handle download completion
    wsClient.on(WS_EVENTS.DOWNLOAD_COMPLETE, (data: DownloadCompleteData) => {
      console.log(`[Wrapper] Download completed: ${data.downloadId}`);
      
      const callback = this.completeCallbacks.get(data.downloadId);
      if (callback) {
        callback(data.filePath);
      }
      
      // Cleanup
      this.cleanupDownload(data.downloadId);
    });

    // Handle download errors
    wsClient.on(WS_EVENTS.DOWNLOAD_ERROR, (data: DownloadErrorData) => {
      console.error(`[Wrapper] Download error for ${data.downloadId}:`, data.error);
      const errorCallback = this.errorCallbacks.get(data.downloadId);
      if (errorCallback) {
        try {
          errorCallback(data.error);
        } catch (callbackError) {
          console.error(`[Wrapper] Error callback failed for ${data.downloadId}:`, callbackError);
        }
      }
      
      // Cleanup failed download
      this.cleanupDownload(data.downloadId);
    });

    // Handle download cancellation
    wsClient.on(WS_EVENTS.DOWNLOAD_CANCELLED, (data: { downloadId: string }) => {
      console.log(`[Wrapper] Download cancelled: ${data.downloadId}`);
      
      // Cleanup cancelled download
      this.cleanupDownload(data.downloadId);
    });
  }

  /**
   * Cleanup download resources
   */
  private async cleanupDownload(downloadId: string): Promise<void> {
    // Remove callbacks
    this.progressCallbacks.delete(downloadId);
    this.completeCallbacks.delete(downloadId);
    this.errorCallbacks.delete(downloadId);
    
    // Unsubscribe from WebSocket updates
    wsClient.unsubscribeFromDownload(downloadId);
    
    // Remove from active downloads
    this.backgroundDownloads.delete(downloadId);
    
    // Update persisted state
    await this.persistActiveDownloads();
  }

  /**
   * Restore active downloads from storage
   */
  private async restoreActiveDownloads(): Promise<void> {
    try {
      const stored = await AsyncStorage.getItem(STORAGE_KEY_DOWNLOADS);
      if (stored) {
        const downloads: BackgroundDownloadTask[] = JSON.parse(stored);
        console.log(`[Wrapper] Restoring ${downloads.length} active downloads`);
        
        for (const download of downloads) {
          this.backgroundDownloads.set(download.id, download);
          
          // Re-subscribe to WebSocket updates
          if (this.isWebSocketConnected) {
            wsClient.subscribeToDownload(download.id);
          }
          
          // Try to resume background download task if it exists
          try {
            const tasks = await RNBackgroundDownloader.checkForExistingDownloads();
            const existingTask = tasks.find((t: any) => t.id === download.id);
            
            if (existingTask) {
              console.log(`[Wrapper] Resuming background task: ${download.id}`);
              this.attachTaskHandlers(download.id, existingTask);
            }
          } catch (error) {
            console.error(`[Wrapper] Failed to resume task ${download.id}:`, error);
          }
        }
      }
    } catch (error) {
      console.error("[Wrapper] Failed to restore active downloads:", error);
    }
  }

  /**
   * Persist active downloads to storage
   */
  private async persistActiveDownloads(): Promise<void> {
    try {
      const downloads = Array.from(this.backgroundDownloads.values()).map((download) => ({
        id: download.id,
        url: download.url,
        destination: download.destination,
      }));
      
      await AsyncStorage.setItem(STORAGE_KEY_DOWNLOADS, JSON.stringify(downloads));
    } catch (error) {
      console.error("[Wrapper] Failed to persist active downloads:", error);
    }
  }

  /**
   * Move file to final destination (SAF)
   */
  private async moveFileToFinalDestination(
    cacheFilePath: string,
    finalFileName: string,
    mimeType?: string
  ): Promise<string> {
    try {
      if (this.finalIsSaf && this.finalDownloadPath) {
        const { StorageAccessFramework } = FileSystem as any;
        const parentUri = this.finalDownloadPath;
        console.log("[Wrapper] SAF write parentUri", parentUri);
        console.log("[Wrapper] Creating SAF file:", finalFileName);

        try {
          const created = await StorageAccessFramework.createFileAsync(
            parentUri,
            finalFileName,
            mimeType || "application/octet-stream"
          );
          console.log("[Wrapper] SAF createFileAsync succeeded, uri:", created);

          try {
            console.log("[Wrapper] Starting SAF copyAsync");
            await FileSystem.copyAsync({ from: cacheFilePath, to: created });
            console.log("[Wrapper] SAF copyAsync succeeded");
          } catch (copyErr) {
            console.error("[Wrapper] SAF copyAsync failed", copyErr);
            return cacheFilePath;
          }

          try {
            await FileSystem.deleteAsync(cacheFilePath, { idempotent: true });
            console.log("[Wrapper] Cache file deleted");
          } catch (e) {
            console.warn("[Wrapper] Failed to delete cache after SAF write", e);
          }
          
          return created;
        } catch (createErr) {
          console.error("[Wrapper] SAF createFileAsync failed:", createErr);
          throw createErr;
        }
      }

      console.error("[Wrapper] No SAF final destination configured");
      return cacheFilePath;
    } catch (error) {
      console.error("[Wrapper] Error saving to SAF:", error);
      return cacheFilePath;
    }
  }

  /**
   * Search for videos (uses backend API)
   */
  async searchVideos(query: string, maxResults: number = 20): Promise<SearchResult> {
    try {
      console.log(`[Wrapper] Searching for: ${query}`);
      return await YouTubeAPI.searchVideos(query, maxResults);
    } catch (error) {
      console.error("[Wrapper] Search failed:", error);
      return {
        videos: [],
        query,
        page: 1,
        hasMore: false,
      };
    }
  }

  /**
   * Get video information (uses backend API)
   */
  async getVideoInfo(url: string): Promise<VideoInfo | null> {
    try {
      console.log(`[Wrapper] Getting video info for: ${url}`);
      return await YouTubeAPI.getVideoInfo(url);
    } catch (error) {
      console.error("[Wrapper] Get video info failed:", error);
      return null;
    }
  }

  /**
   * Get playlist videos (not implemented - requires backend support)
   */
  async getPlaylistVideos(url: string): Promise<VideoInfo[]> {
    console.warn("[Wrapper] Playlist support not implemented in backend version");
    return [];
  }

  /**
   * Attach progress handlers to background download task
   */
  private attachTaskHandlers(downloadId: string, task: any): void {
    const download = this.backgroundDownloads.get(downloadId);
    if (!download) {
      return;
    }

    download.task = task;

    task
      .begin((expectedBytes: number) => {
        console.log(`[Wrapper] Download begin: ${downloadId}, size: ${expectedBytes}`);
      })
      .progress((percent: number, bytesWritten: number, bytesTotal: number) => {
        const progress = Math.round(percent * 100);
        console.log(`[Wrapper] Background download progress: ${progress}%`);
        
        const callback = this.progressCallbacks.get(downloadId);
        if (callback) {
          callback(progress);
        }
      })
      .done(async () => {
        console.log(`[Wrapper] Background download completed: ${downloadId}`);
        
        // Move to final destination
        const finalPath = await this.moveFileToFinalDestination(
          download.destination,
          download.destination.split("/").pop() || "video.mp4"
        );
        
        const callback = this.completeCallbacks.get(downloadId);
        if (callback) {
          callback(finalPath);
        }
        
        // Cleanup
        await this.cleanupDownload(downloadId);
      })
      .error((error: string) => {
        console.error(`[Wrapper] Background download error: ${downloadId}`, error);
        this.cleanupDownload(downloadId);
      });
  }

  /**
   * Download video
   */
  async downloadVideo(
    url: string,
    formatType: "mp4" | "mp3",
    progressCallback?: (progress: number) => void,
    completeCallback?: (filename: string) => void,
    errorCallback?: (error: string) => void
  ): Promise<boolean> {
    try {
      if (!this.cachePath) {
        console.warn("[Wrapper] Cache path not initialized");
        return false;
      }

      console.log(`[Wrapper] Initiating download: ${url} (${formatType})`);

      // Step 1: Initiate download on backend
      const downloadInfo = await YouTubeAPI.initiateDownload(url, formatType);
      
      console.log(`[Wrapper] Download info received:`, {
        downloadId: downloadInfo.downloadId,
        fileName: downloadInfo.fileName,
        downloadUrl: downloadInfo.downloadUrl,
      });

      // Store callbacks
      if (progressCallback) {
        this.progressCallbacks.set(downloadInfo.downloadId, progressCallback);
      }
      if (completeCallback) {
        this.completeCallbacks.set(downloadInfo.downloadId, completeCallback);
      }
      if (errorCallback) {
        this.errorCallbacks.set(downloadInfo.downloadId, errorCallback);
      }

      // Subscribe to WebSocket updates
      wsClient.subscribeToDownload(downloadInfo.downloadId);

      // Step 2: Start background download using react-native-background-downloader
      const destination = `${this.cachePath}${downloadInfo.fileName}`;
      
      console.log(`[Wrapper] Starting background download to: ${destination}`);
      
      const task = RNBackgroundDownloader.download({
        id: downloadInfo.downloadId,
        url: downloadInfo.downloadUrl,
        destination,
      });

      // Store download info
      const download: BackgroundDownloadTask = {
        id: downloadInfo.downloadId,
        url: downloadInfo.downloadUrl,
        destination,
        task,
      };
      
      this.backgroundDownloads.set(downloadInfo.downloadId, download);
      
      // Persist state
      await this.persistActiveDownloads();

      // Attach handlers
      this.attachTaskHandlers(downloadInfo.downloadId, task);

      return true;
    } catch (error) {
      console.error("[Wrapper] Download failed:", error);
      return false;
    }
  }

  /**
   * Resume download
   */
  async resumeDownload(downloadId: string): Promise<boolean> {
    try {
      console.log(`[Wrapper] Resuming download: ${downloadId}`);
      
      const download = this.backgroundDownloads.get(downloadId);
      if (!download || !download.task) {
        console.error("[Wrapper] Download task not found");
        return false;
      }

      // Resume on backend via WebSocket
      wsClient.resumeDownload(downloadId);
      
      // Resume background task
      download.task.resume();
      
      return true;
    } catch (error) {
      console.error("[Wrapper] Resume download failed:", error);
      return false;
    }
  }

  /**
   * Pause download
   */
  async pauseDownload(downloadId: string): Promise<boolean> {
    try {
      console.log(`[Wrapper] Pausing download: ${downloadId}`);
      
      const download = this.backgroundDownloads.get(downloadId);
      if (!download || !download.task) {
        console.error("[Wrapper] Download task not found");
        return false;
      }

      // Pause background task
      download.task.pause();
      
      return true;
    } catch (error) {
      console.error("[Wrapper] Pause download failed:", error);
      return false;
    }
  }

  /**
   * Cancel download
   */
  async cancelDownload(downloadId: string): Promise<boolean> {
    try {
      console.log(`[Wrapper] Cancelling download: ${downloadId}`);
      
      const download = this.backgroundDownloads.get(downloadId);
      if (!download) {
        console.error("[Wrapper] Download not found");
        return false;
      }

      // Cancel on backend
      await YouTubeAPI.cancelDownload(downloadId);
      
      // Cancel via WebSocket
      wsClient.cancelDownload(downloadId);
      
      // Stop background task
      if (download.task) {
        download.task.stop();
      }

      // Cleanup
      await this.cleanupDownload(downloadId);
      
      return true;
    } catch (error) {
      console.error("[Wrapper] Cancel download failed:", error);
      return false;
    }
  }

  /**
   * Get all active downloads
   */
  getActiveDownloads(): string[] {
    return Array.from(this.backgroundDownloads.keys());
  }

  /**
   * Cleanup on destroy
   */
  destroy(): void {
    console.log("[Wrapper] Destroying wrapper instance");
    
    // Disconnect WebSocket
    wsClient.disconnect();
    
    // Clear all callbacks
    this.progressCallbacks.clear();
    this.completeCallbacks.clear();
  }
}
