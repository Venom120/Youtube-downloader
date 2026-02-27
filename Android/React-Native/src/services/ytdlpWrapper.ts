import { Innertube } from "youtubei.js";
import * as FileSystem from "expo-file-system/legacy";
import * as MediaLibrary from 'expo-media-library';
import { VideoInfo, SearchResult } from "../models/videoModel";

type StreamFormat = {
  url?: string;
  mime_type?: string;
  bitrate?: number;
  has_audio?: boolean;
  has_video?: boolean;
  quality_label?: string;
};

type StreamingData = {
  formats?: StreamFormat[];
  adaptive_formats?: StreamFormat[];
};

const extractVideoId = (value: string): string | null => {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }

  if (/^[a-zA-Z0-9_-]{11}$/.test(trimmed)) {
    return trimmed;
  }

  const match = trimmed.match(/[?&]v=([^&]+)/) || trimmed.match(/youtu\.be\/([^?&]+)/);
  return match ? match[1] : null;
};

const extractPlaylistId = (value: string): string | null => {
  const match = value.match(/[?&]list=([^&]+)/);
  return match ? match[1] : null;
};

const sanitizeFilename = (name: string): string => {
  return name.replace(/[<>:"/\\|?*]+/g, "").trim() || "video";
};

const getItemId = (item: Record<string, unknown>): string => {
  const id = item.id || item.video_id || item.videoId;
  return typeof id === "string" ? id : "";
};

const getItemTitle = (item: Record<string, unknown>): string => {
  const title = item.title;
  if (typeof title === "string") {
    return title;
  }

  if (title && typeof title === "object" && "text" in title) {
    const textValue = (title as { text?: unknown }).text;
    return typeof textValue === "string" ? textValue : "Unknown";
  }

  return "Unknown";
};

const getItemThumbnail = (item: Record<string, unknown>): string => {
  const thumbs = item.thumbnails;
  if (Array.isArray(thumbs) && thumbs.length > 0) {
    const url = (thumbs[0] as { url?: unknown }).url;
    return typeof url === "string" ? url : "";
  }
  return "";
};

const getItemDuration = (item: Record<string, unknown>): number => {
  const duration = item.duration;
  if (typeof duration === "number") {
    return duration;
  }

  if (duration && typeof duration === "object" && "seconds" in duration) {
    const seconds = (duration as { seconds?: unknown }).seconds;
    return typeof seconds === "number" ? seconds : 0;
  }

  return 0;
};

const getItemAuthor = (item: Record<string, unknown>): string => {
  const author = item.author;
  if (typeof author === "string") {
    return author;
  }

  if (author && typeof author === "object" && "name" in author) {
    const name = (author as { name?: unknown }).name;
    return typeof name === "string" ? name : "Unknown";
  }

  return "Unknown";
};

const getItemViewCount = (item: Record<string, unknown>): number | undefined => {
  const viewCount = item.view_count ?? item.viewCount;
  return typeof viewCount === "number" ? viewCount : undefined;
};

const getItemPublished = (item: Record<string, unknown>): string | undefined => {
  const published = item.published;
  if (typeof published === "string") {
    return published;
  }

  if (published && typeof published === "object" && "text" in published) {
    const textValue = (published as { text?: unknown }).text;
    return typeof textValue === "string" ? textValue : undefined;
  }

  return undefined;
};

const getItemUrl = (item: Record<string, unknown>, fallbackId: string): string => {
  const url = item.url;
  if (typeof url === "string") {
    return url;
  }

  return fallbackId ? `https://youtube.com/watch?v=${fallbackId}` : "";
};

export class YTDLPWrapper {
  private client?: Innertube;
  private cachePath: string;
  private finalDownloadPath: string;
  private finalIsSaf: boolean;
  public readonly libName = "youtubei.js";

  constructor(cachePath?: string, finalDownloadPath?: string, finalIsSaf: boolean = false) {
    this.cachePath = this.normalizeDirUri(cachePath);
    this.finalDownloadPath = finalDownloadPath || ""; // store raw SAF uri or path
    this.finalIsSaf = !!finalIsSaf;
  }

  private async getClient(): Promise<Innertube> {
    if (!this.client) {
      this.client = await Innertube.create();
    }

    return this.client;
  }

  private normalizeDirUri(path?: string): string {
    if (!path || typeof path !== "string") {
      return "";
    }

    return path.endsWith("/") ? path : `${path}/`;
  }

  private async moveFileToFinalDestination(cacheFilePath: string, finalFileName: string, mimeType?: string): Promise<string> {
    try {
      // If we were given a SAF directory URI, write into it via StorageAccessFramework
      if (this.finalIsSaf && this.finalDownloadPath) {
        try {
          const { StorageAccessFramework, EncodingType } = FileSystem;
          const parentUri = this.finalDownloadPath; // SAF directory URI
          // create an empty file and get its SAF uri
          const created = await StorageAccessFramework.createFileAsync(parentUri, finalFileName, mimeType || 'application/octet-stream');
          // Read cache as base64 and write into the SAF file
          const b64 = await FileSystem.readAsStringAsync(cacheFilePath, { encoding: EncodingType.Base64 });
          await FileSystem.writeAsStringAsync(created, b64, { encoding: EncodingType.Base64 });
          // attempt to delete cache
          try { await FileSystem.deleteAsync(cacheFilePath, { idempotent: true }); } catch (e) {}
          return created;
        } catch (safErr) {
          console.warn('Failed to write via SAF, falling back to media-library', safErr);
          // fallback to media library below
        }
      }

      // Save the downloaded cache file into the user's media library (Downloads/album)
      const asset = await MediaLibrary.createAssetAsync(cacheFilePath);
      const albumName = "YTDownloader";
      try {
        // Try create album; if it exists, add asset to it
        await MediaLibrary.createAlbumAsync(albumName, asset, false);
      } catch (e: any) {
        if (e?.message && e.message.includes('Album already exists')) {
          await MediaLibrary.addAssetsToAlbumAsync([asset], albumName, false);
        } else if (e?.code === 'E_ALREADY_EXISTS') {
          await MediaLibrary.addAssetsToAlbumAsync([asset], albumName, false);
        } else {
          // fallback: try to add anyway
          try {
            await MediaLibrary.addAssetsToAlbumAsync([asset], albumName, false);
          } catch (err) {
            console.warn('Failed to add asset to album, but asset exists in library', err);
          }
        }
      }

      // Delete cache file after importing
      try {
        await FileSystem.deleteAsync(cacheFilePath, { idempotent: true });
      } catch (delErr) {
        // non-fatal
      }

      return asset.uri;
    } catch (error) {
      console.error("Error saving to media library:", error);
      return cacheFilePath;
    }
  }

  private pickStreamUrl(streaming: StreamingData, formatType: "mp4" | "mp3"): { url: string; extension: string } | null {
    const formats = [...(streaming.formats || []), ...(streaming.adaptive_formats || [])].filter(
      (format) => !!format.url
    );

    if (!formats.length) {
      return null;
    }

    if (formatType === "mp3") {
      const audioFormats = formats.filter((format) => format.mime_type?.includes("audio"));
      const preferred = audioFormats.sort((a, b) => (b.bitrate || 0) - (a.bitrate || 0));
      const chosen = preferred[0] || formats[0];
      const extension = chosen.mime_type?.includes("audio/mp4") ? "m4a" : "webm";
      return chosen.url ? { url: chosen.url, extension } : null;
    }

    const mp4Formats = formats.filter((format) => format.mime_type?.includes("video/mp4"));
    const withAudio = mp4Formats.find((format) => format.has_audio);
    const chosen = withAudio || mp4Formats[0] || formats[0];
    return chosen.url ? { url: chosen.url, extension: "mp4" } : null;
  }

  async getVideoInfo(url: string): Promise<VideoInfo | null> {
    const client = await this.getClient();
    const videoId = extractVideoId(url);

    if (!videoId) {
      return null;
    }

    try {
      const info = await client.getInfo(videoId);
      const basicInfo = info.basic_info as Record<string, unknown>;
      const thumbList = (basicInfo.thumbnail as Array<{ url?: string }> | undefined) || [];
      const thumbnail = thumbList[0]?.url || "";
      const duration = typeof basicInfo.duration === "number" ? basicInfo.duration : 0;
      const viewCount = typeof basicInfo.view_count === "number" ? basicInfo.view_count : undefined;

      return {
        videoId,
        title: typeof basicInfo.title === "string" ? basicInfo.title : "Unknown",
        thumbnailUrl: thumbnail,
        duration,
        channel: typeof basicInfo.author === "string" ? basicInfo.author : "Unknown",
        viewCount,
        uploadDate: typeof (basicInfo as { publish_date?: unknown }).publish_date === "string"
          ? (basicInfo as { publish_date: string }).publish_date
          : undefined,
        url,
        isPlaylist: false,
      };
    } catch (error) {
      console.warn("getVideoInfo failed", error);
      return null;
    }
  }

  async getPlaylistVideos(url: string): Promise<VideoInfo[]> {
    const client = await this.getClient();
    const playlistId = extractPlaylistId(url);

    if (!playlistId) {
      return [];
    }

    try {
      const playlist = await client.getPlaylist(playlistId);
      const videos = ((playlist?.videos || []) as unknown) as Array<Record<string, unknown>>;

      return videos.map((item) => {
        const id = getItemId(item);
        return {
          videoId: id,
          title: getItemTitle(item),
          thumbnailUrl: getItemThumbnail(item),
          duration: getItemDuration(item),
          channel: getItemAuthor(item),
          viewCount: getItemViewCount(item),
          uploadDate: getItemPublished(item),
          url: getItemUrl(item, id),
          isPlaylist: false,
        };
      });
    } catch (error) {
      console.warn("getPlaylistVideos failed", error);
      return [];
    }
  }

  async searchVideos(query: string, maxResults: number = 20): Promise<SearchResult> {
    const client = await this.getClient();

    try {
      const result = await client.search(query, { type: "video" });
      const videos = (((result.videos || []) as unknown) as Array<Record<string, unknown>>)
        .slice(0, maxResults)
        .map((item) => {
          const id = getItemId(item);
          return {
            videoId: id,
            title: getItemTitle(item),
            thumbnailUrl: getItemThumbnail(item),
            duration: getItemDuration(item),
            channel: getItemAuthor(item),
            viewCount: getItemViewCount(item),
            url: getItemUrl(item, id),
            isPlaylist: false,
          };
        });

      return {
        videos,
        query,
        page: 1,
        hasMore: videos.length >= maxResults,
      };
    } catch (error) {
      console.warn("searchVideos failed", error);
      return {
        videos: [],
        query,
        page: 1,
        hasMore: false,
      };
    }
  }

  async downloadVideo(
    url: string,
    formatType: "mp4" | "mp3",
    progressCallback?: (progress: number) => void,
    completeCallback?: (filename: string) => void
  ): Promise<boolean> {
    const client = await this.getClient();
    const videoId = extractVideoId(url);
    if (!videoId) {
      return false;
    }

    try {
      if (!this.cachePath) {
        console.warn("Cache path not initialized");
        return false;
      }

      const info = await client.getInfo(videoId);
      const streaming = info.streaming_data as StreamingData | undefined;
      if (!streaming) {
        return false;
      }

      const chosen = this.pickStreamUrl(streaming, formatType);
      if (!chosen) {
        return false;
      }

      const title = sanitizeFilename(info.basic_info.title || "video");
      const fileName = `${title}.${chosen.extension}`;
      const cacheFilePath = `${this.cachePath}${fileName}`;
      const targetPath = cacheFilePath;

      const resumable = FileSystem.createDownloadResumable(
        chosen.url,
        targetPath,
        {},
        (progress) => {
          const total = progress.totalBytesExpectedToWrite || 0;
          const written = progress.totalBytesWritten || 0;
          if (total > 0 && progressCallback) {
            progressCallback(Math.min(100, (written / total) * 100));
          }
        }
      );

      await resumable.downloadAsync();

      const finalPath = await this.moveFileToFinalDestination(cacheFilePath, fileName);

      if (completeCallback) {
        completeCallback(finalPath);
      }
      return true;
    } catch (error) {
      console.warn("downloadVideo failed", error);
      return false;
    }
  }
}
