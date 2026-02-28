import { backendClient } from "./backendClient";
import { API_ENDPOINTS } from "./config";
import { VideoInfo, SearchResult } from "../models/videoModel";

/**
 * Backend response types
 */
export type BackendVideoInfo = {
  videoId: string;
  title: string;
  thumbnailUrl: string;
  duration: number;
  channel: string;
  viewCount: number;
  uploadDate?: string;
  url: string;
};

export type BackendSearchResult = {
  videos: BackendVideoInfo[];
  query: string;
  page: number;
  hasMore: boolean;
};

export type InitiateDownloadResponse = {
  downloadId: string;
  videoId: string;
  downloadUrl: string;
  fileName: string;
  fileSize?: number;
  format: string;
  message: string;
};

export type DownloadStatusResponse = {
  downloadId: string;
  status: "pending" | "downloading" | "completed" | "failed" | "cancelled";
  progress: number;
  downloadedBytes: number;
  totalBytes: number;
  error?: string;
};

/**
 * YouTube API functions using backend server
 */
export class YouTubeAPI {
  /**
   * Search for videos
   */
  static async searchVideos(query: string, maxResults: number = 20): Promise<SearchResult> {
    try {
      console.log(`[YouTube API] Searching for: ${query}`);
      
      const response = await backendClient.post<BackendSearchResult>(API_ENDPOINTS.SEARCH, {
        query,
        maxResults,
      });

      // Convert backend format to app format
      const videos: VideoInfo[] = response.videos.map((video) => ({
        videoId: video.videoId,
        title: video.title,
        thumbnailUrl: video.thumbnailUrl,
        duration: video.duration,
        channel: video.channel,
        viewCount: video.viewCount,
        uploadDate: video.uploadDate,
        url: video.url,
        isPlaylist: false,
      }));

      return {
        videos,
        query: response.query,
        page: response.page || 1,
        hasMore: response.hasMore || false,
      };
    } catch (error) {
      console.error("[YouTube API] Search failed:", error);
      throw error;
    }
  }

  /**
   * Get video information
   */
  static async getVideoInfo(url: string): Promise<VideoInfo | null> {
    try {
      console.log(`[YouTube API] Fetching video info for: ${url}`);
      
      const response = await backendClient.post<BackendVideoInfo>(API_ENDPOINTS.VIDEO_INFO, {
        url,
      });

      return {
        videoId: response.videoId,
        title: response.title,
        thumbnailUrl: response.thumbnailUrl,
        duration: response.duration,
        channel: response.channel,
        viewCount: response.viewCount,
        uploadDate: response.uploadDate,
        url: response.url,
        isPlaylist: false,
      };
    } catch (error) {
      console.error("[YouTube API] Get video info failed:", error);
      return null;
    }
  }

  /**
   * Initiate video download
   * Returns download URL and metadata from backend
   */
  static async initiateDownload(
    url: string,
    formatType: "mp4" | "mp3"
  ): Promise<InitiateDownloadResponse> {
    try {
      console.log(`[YouTube API] Initiating download: ${url} (${formatType})`);
      
      const response = await backendClient.post<InitiateDownloadResponse>(API_ENDPOINTS.DOWNLOAD, {
        url,
        format: formatType,
      });

      console.log(`[YouTube API] Download initiated: ${response.downloadId}`);
      return response;
    } catch (error) {
      console.error("[YouTube API] Initiate download failed:", error);
      throw error;
    }
  }

  /**
   * Get download status
   */
  static async getDownloadStatus(downloadId: string): Promise<DownloadStatusResponse> {
    try {
      const response = await backendClient.get<DownloadStatusResponse>(
        `${API_ENDPOINTS.DOWNLOAD_STATUS}/${downloadId}`
      );
      return response;
    } catch (error) {
      console.error("[YouTube API] Get download status failed:", error);
      throw error;
    }
  }

  /**
   * Cancel download
   */
  static async cancelDownload(downloadId: string): Promise<void> {
    try {
      console.log(`[YouTube API] Cancelling download: ${downloadId}`);
      
      await backendClient.post(API_ENDPOINTS.CANCEL_DOWNLOAD, {
        downloadId,
      });
      
      console.log(`[YouTube API] Download cancelled: ${downloadId}`);
    } catch (error) {
      console.error("[YouTube API] Cancel download failed:", error);
      throw error;
    }
  }
}

export default YouTubeAPI;
