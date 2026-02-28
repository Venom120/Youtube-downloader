import * as FileSystem from "expo-file-system/legacy";
import { VideoInfo, SearchResult } from "../models/videoModel";
import { ClientType, Innertube } from "youtubei.js";
import { parseViewCount } from "../utils/format";

// Global Innertube instance - lazy initialized
let innertube: Innertube | null = null;
let initPromise: Promise<Innertube> | null = null;

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

/**
 * Force reset the Innertube instance.
 * Useful when the session becomes stale or needs to be refreshed.
 */
function resetInnertubeInstance(): void {
  console.log("Resetting Innertube instance");
  innertube = null;
  initPromise = null;
}

/**
 * Initialize or return the global Innertube instance.
 * Uses lazy initialization with caching to optimize performance.
 */
async function getInnertubeInstance(): Promise<Innertube> {
  // Return cached instance if available
  if (innertube) {
    return innertube;
  }

  // Return pending promise if initialization is in progress
  if (initPromise) {
    return initPromise;
  }

  // Start new initialization
  initPromise = Innertube.create({
    // Generate session locally for better performance in React Native
    generate_session_locally: true,
    // Enable session caching to reuse across app restarts
    enable_session_cache: true,
    // Use DESKTOP as device category
    device_category: "desktop",
    // Use WEB client - most reliable for both search and video info
    client_type: ClientType.WEB,
    // Set language and location
    lang: "en",
    location: "US",
    // CRITICAL: Enable player retrieval for streaming data
    retrieve_player: true,
  });

  try {
    innertube = await initPromise;
    console.log("Innertube instance initialized successfully");
    return innertube;
  } catch (error) {
    console.error("Failed to initialize Innertube:", error);
    initPromise = null;
    throw error;
  }
}

export class YTDLPWrapper {
  private cachePath: string;
  private finalDownloadPath: string;
  private finalIsSaf: boolean;
  public readonly libName = "YouTubei.js (InnerTube API)";

  constructor(cachePath?: string, finalDownloadPath?: string, finalIsSaf: boolean = false) {
    this.cachePath = this.normalizeDirUri(cachePath);
    this.finalDownloadPath = finalDownloadPath || "";
    this.finalIsSaf = !!finalIsSaf;
  }

  private normalizeDirUri(path?: string): string {
    if (!path || typeof path !== "string") {
      return "";
    }
    return path.endsWith("/") ? path : `${path}/`;
  }

  private async moveFileToFinalDestination(cacheFilePath: string, finalFileName: string, mimeType?: string): Promise<string> {
    try {
      if (this.finalIsSaf && this.finalDownloadPath) {
        const { StorageAccessFramework } = FileSystem as any;
        const parentUri = this.finalDownloadPath;
        console.log('SAF write parentUri', parentUri);
        console.log('Creating SAF file:', finalFileName, 'mimeType:', mimeType);
        
        try {
          const created = await StorageAccessFramework.createFileAsync(parentUri, finalFileName, mimeType || 'application/octet-stream');
          console.log('SAF createFileAsync succeeded, uri:', created);

          try {
            console.log('Starting SAF copyAsync from cache to SAF URI');
            await FileSystem.copyAsync({ from: cacheFilePath, to: created });
            console.log('SAF copyAsync succeeded', { from: cacheFilePath, to: created });
          } catch (copyErr) {
            console.error('SAF copyAsync failed', copyErr);
            console.warn('Returning cache path due to SAF copy failure');
            return cacheFilePath;
          }
          
          try {
            await FileSystem.deleteAsync(cacheFilePath, { idempotent: true });
            console.log('Cache file deleted successfully');
          } catch (e) {
            console.warn('Failed to delete cache after SAF write', e);
          }
          return created;
        } catch (createErr) {
          console.error('SAF createFileAsync failed:', createErr);
          throw createErr;
        }
      }

      console.error('No SAF final destination configured; cannot move file to external Downloads.');
      return cacheFilePath;
    } catch (error) {
      console.error("Error saving to SAF final destination:", error);
      return cacheFilePath;
    }
  }

  async getVideoInfo(url: string): Promise<VideoInfo | null> {
    const videoId = extractVideoId(url);
    if (!videoId) {
      console.warn("getVideoInfo: No valid video ID extracted from URL:", url);
      return null;
    }

    try {
      const yt = await getInnertubeInstance();
      console.log("getVideoInfo: Fetching video info for:", videoId);
      
      // Use getBasicInfo as it's faster and doesn't require deciphering
      const videoInfo = await yt.getBasicInfo(videoId);
      
      if (!videoInfo) {
        console.error("getVideoInfo: No data returned from getBasicInfo");
        return null;
      }

      console.log("getVideoInfo: Successfully retrieved video info");
      
      const basicInfo = videoInfo.basic_info as any;
      
      // Extract thumbnail
      const thumbnailUrl = basicInfo?.thumbnail?.[0]?.url || basicInfo?.thumbnails?.[0]?.url || "";
      
      // Extract title
      let title = "Unknown";
      if (typeof basicInfo?.title === "string") {
        title = basicInfo.title;
      } else if (basicInfo?.title?.text) {
        title = basicInfo.title.text;
      } else if (basicInfo?.title?.runs?.[0]?.text) {
        title = basicInfo.title.runs[0].text;
      }
      
      // Parse duration from length_text or duration properties
      let duration = basicInfo?.duration || 0;
      if (typeof basicInfo?.length_text === "string") {
        const timeParts = basicInfo.length_text.split(":");
        if (timeParts.length === 2) {
          duration = parseInt(timeParts[0]) * 60 + parseInt(timeParts[1]);
        } else if (timeParts.length === 3) {
          duration = parseInt(timeParts[0]) * 3600 + parseInt(timeParts[1]) * 60 + parseInt(timeParts[2]);
        }
      } else if (basicInfo?.length_text?.text) {
        const timeParts = basicInfo.length_text.text.split(":");
        if (timeParts.length === 2) {
          duration = parseInt(timeParts[0]) * 60 + parseInt(timeParts[1]);
        } else if (timeParts.length === 3) {
          duration = parseInt(timeParts[0]) * 3600 + parseInt(timeParts[1]) * 60 + parseInt(timeParts[2]);
        }
      }
      
      // Extract view count
      const viewCountText = basicInfo?.short_view_count?.text || basicInfo?.view_count?.text || "";
      
      return {
        videoId: basicInfo?.video_id || basicInfo?.id || videoId,
        title,
        thumbnailUrl,
        duration,
        channel: basicInfo?.author?.name || "Unknown",
        viewCount: parseViewCount(viewCountText),
        uploadDate: basicInfo?.published?.text || undefined,
        url,
        isPlaylist: false,
      };
    } catch (error) {
      console.error("getVideoInfo failed:", error);
      return null;
    }
  }

  async getPlaylistVideos(url: string): Promise<VideoInfo[]> {
    const playlistId = extractPlaylistId(url);
    if (!playlistId) {
      return [];
    }

    try {
      const yt = await getInnertubeInstance();
      console.log("getPlaylistVideos: Fetching playlist with Innertube:", playlistId);
      
      const playlist = await yt.getPlaylist(playlistId);
      
      if (!playlist || !playlist.videos || playlist.videos.length === 0) {
        console.log("getPlaylistVideos: No videos found in playlist");
        return [];
      }

      console.log("getPlaylistVideos: Found", playlist.videos.length, "videos");

      // DEBUG: Log first video structure from playlist
      if (playlist.videos.length > 0) {
  
      }

      // Map playlist videos to our VideoInfo format
      return playlist.videos.map((video: any) => {
        const videoId = video.video_id || video.id || "";
        const thumbnailUrl = video.thumbnails?.[0]?.url || video.thumbnail?.[0]?.url || "";
        
        // Extract title from either text property or runs array
        let title = "Unknown";
        if (typeof video.title === "string") {
          title = video.title;
        } else if (video.title?.text) {
          title = video.title.text;
        } else if (video.title?.runs?.[0]?.text) {
          title = video.title.runs[0].text;
        }
        
        // Parse duration from length_text (e.g., "3:49" to seconds)
        let duration = 0;
        if (video.length_text?.text) {
          const timeParts = video.length_text.text.split(":");
          if (timeParts.length === 2) {
            duration = parseInt(timeParts[0]) * 60 + parseInt(timeParts[1]);
          } else if (timeParts.length === 3) {
            duration = parseInt(timeParts[0]) * 3600 + parseInt(timeParts[1]) * 60 + parseInt(timeParts[2]);
          }
        } else if (typeof video.duration === "number") {
          duration = video.duration;
        }
        
        // Extract view count from short_view_count or view_count
        const viewCountText = video.short_view_count?.text || video.view_count?.text || "";
        
        return {
          videoId,
          title,
          thumbnailUrl,
          duration,
          channel: video.author?.name || "Unknown",
          viewCount: parseViewCount(viewCountText),
          uploadDate: video.published?.text || undefined,
          url: `https://youtube.com/watch?v=${videoId}`,
          isPlaylist: false,
        };
      });
    } catch (error) {
      console.error("getPlaylistVideos failed:", error);
      return [];
    }
  }

  async searchVideos(query: string, maxResults: number = 20): Promise<SearchResult> {
    try {
      const yt = await getInnertubeInstance();
      console.log("searchVideos: Searching with Innertube for:", query);
      
      // Use search method with filters to get only videos
      const searchResults = await yt.search(query, {
        type: "video", // Filter to only videos
      });
      
      if (!searchResults || !searchResults.videos || searchResults.videos.length === 0) {
        console.log("searchVideos: No results found");
        return {
          videos: [],
          query,
          page: 1,
          hasMore: false,
        };
      }

      console.log("searchVideos: Found", searchResults.videos.length, "results");
      


      // Map search results to our VideoInfo format
      const videos = searchResults.videos
        .slice(0, maxResults)
        .map((video: any) => {
          const videoId = video.video_id || video.id || "";
          const thumbnailUrl = video.thumbnails?.[0]?.url || "";
          
          // Extract title from either text property or runs array
          let title = "Unknown";
          if (typeof video.title === "string") {
            title = video.title;
          } else if (video.title?.text) {
            title = video.title.text;
          } else if (video.title?.runs?.[0]?.text) {
            title = video.title.runs[0].text;
          }
          
          // Parse duration from length_text (e.g., "3:49" to seconds)
          let duration = 0;
          if (video.length_text?.text) {
            const timeParts = video.length_text.text.split(":");
            if (timeParts.length === 2) {
              duration = parseInt(timeParts[0]) * 60 + parseInt(timeParts[1]);
            } else if (timeParts.length === 3) {
              duration = parseInt(timeParts[0]) * 3600 + parseInt(timeParts[1]) * 60 + parseInt(timeParts[2]);
            }
          }
          
          // Extract view count from short_view_count or view_count
          const viewCountText = video.short_view_count?.text || video.view_count?.text || "";
          
          // Extract channel name
          const channel = video.author?.name || "Unknown";
          
          // Extract upload date
          const uploadDate = video.published?.text || undefined;
          
          return {
            videoId,
            title,
            thumbnailUrl,
            duration,
            channel,
            viewCount: parseViewCount(viewCountText),
            uploadDate,
            url: `https://youtube.com/watch?v=${videoId}`,
            isPlaylist: false,
          };
        });

      return {
        videos,
        query,
        page: 1,
        hasMore: searchResults.has_continuation || false,
      };
    } catch (error) {
      console.error("searchVideos failed:", error);
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
    const videoId = extractVideoId(url);
    if (!videoId) {
      return false;
    }

    try {
      if (!this.cachePath) {
        console.warn("Cache path not initialized");
        return false;
      }

      console.log("downloadVideo init", {
        url,
        videoId,
        cachePath: this.cachePath,
        finalDownloadPath: this.finalDownloadPath,
        finalIsSaf: this.finalIsSaf,
        formatType,
      });

      const yt = await getInnertubeInstance();
      
      // Get full video info including streaming data
      console.log("Fetching video info from Innertube for videoId:", videoId);
      
      let videoInfo: any = null;
      try {
        videoInfo = await yt.getInfo(videoId);
      } catch (infoError) {
        console.error("Failed to get video info:", infoError);
        console.error("Error details:", {
          message: (infoError as any)?.message,
          code: (infoError as any)?.code,
        });
        return false;
      }
      
      console.log("DEBUG videoInfo received:", {
        exists: !!videoInfo,
        type: typeof videoInfo,
        keys: videoInfo ? Object.keys(videoInfo) : [],
      });
      
      if (!videoInfo) {
        console.error("Failed to get video info");
        return false;
      }

      console.log("DEBUG videoInfo.basic_info:", {
        exists: !!videoInfo.basic_info,
        type: typeof videoInfo.basic_info,
        keys: videoInfo.basic_info ? Object.keys(videoInfo.basic_info) : [],
      });

      // Check playability status first
      const playabilityStatus = videoInfo.playability_status;
      console.log("DEBUG playability_status:", {
        status: playabilityStatus?.status,
        reason: playabilityStatus?.reason,
        embeddable: playabilityStatus?.embeddable,
      });

      if (playabilityStatus?.status === "UNPLAYABLE" || playabilityStatus?.status === "LOGIN_REQUIRED") {
        console.error("Video is not playable:", playabilityStatus?.reason);
        console.error("Full playability_status:", playabilityStatus);
        console.error("This may be due to:");
        console.error("1. Video being age-restricted, private, or region-locked");
        console.error("2. YouTube detecting automated requests (bot detection)");
        console.error("3. Video requiring sign-in");
        console.error("");
        console.error("Try:");
        console.error("1. Restart the app to refresh the YouTube session");
        console.error("2. Try a different video");
        console.error("3. Wait a few minutes and try again");
        
        return false;
      }

      console.log("DEBUG videoInfo.streaming_data:", {
        exists: !!videoInfo.streaming_data,
        type: typeof videoInfo.streaming_data,
        keys: videoInfo.streaming_data ? Object.keys(videoInfo.streaming_data) : [],
      });

      // Check if streaming data exists
      if (!videoInfo.streaming_data) {
        console.error("No streaming data in video info");
        return false;
      }

      // Get formats from streaming data
      console.log("Extracting formats from streaming_data");
      const streamingData = videoInfo.streaming_data;
      
      console.log("DEBUG streamingData:", {
        exists: !!streamingData,
        type: typeof streamingData,
        keys: streamingData ? Object.keys(streamingData) : [],
        has_formats: !!(streamingData as any)?.formats,
        formats_length: (streamingData as any)?.formats?.length,
        has_adaptive_formats: !!(streamingData as any)?.adaptive_formats,
        adaptive_formats_length: (streamingData as any)?.adaptive_formats?.length,
      });

      // Combine formats and adaptive_formats
      const allFormats = [
        ...((streamingData as any)?.formats || []),
        ...((streamingData as any)?.adaptive_formats || []),
      ];

      console.log("DEBUG allFormats combined:", {
        length: allFormats.length,
        isArray: Array.isArray(allFormats),
      });

      if (allFormats.length === 0) {
        console.error("No formats available in streaming data");
        return false;
      }

      const formats = allFormats;
      
      console.log("DEBUG formats array:", {
        length: formats.length,
        isArray: Array.isArray(formats),
        firstFormatType: formats[0] ? typeof formats[0] : "undefined",
        firstFormatKeys: formats[0] ? Object.keys(formats[0]) : [],
      });
      
      if (formats.length === 0) {
        console.error("No formats available in streaming data");
        return false;
      }

      // Log all available formats
      console.log("DEBUG All formats:");
      formats.forEach((fmt: any, index: number) => {
        console.log(`  Format ${index}:`, {
          mime_type: fmt.mime_type,
          has_url: !!fmt.url,
          has_decipher: !!fmt.decipher,
          bitrate: fmt.bitrate,
          width: fmt.width,
          height: fmt.height,
          quality_label: fmt.quality_label,
        });
      });

      // Check if videoInfo has a download method we can use directly
      console.log("DEBUG Checking videoInfo.download method:", {
        hasDownload: typeof (videoInfo as any).download === 'function',
        hasChooseFormat: typeof (videoInfo as any).chooseFormat === 'function',
      });

      // First, check if any formats have direct URLs (no deciphering needed)
      const formatsWithUrls = formats.filter((fmt: any) => !!fmt.url);
      console.log("DEBUG Formats with direct URLs:", {
        count: formatsWithUrls.length,
        formats: formatsWithUrls.map((fmt: any) => ({
          mime_type: fmt.mime_type,
          quality_label: fmt.quality_label,
          has_url: !!fmt.url,
        })),
      });

      // Select appropriate format based on formatType
      let selectedFormat = null;
      
      console.log(`DEBUG Selecting format for type: ${formatType}`);
      
      if (formatType === "mp3") {
        // Get audio only formats, sorted by bitrate
        const audioFormats = formats.filter((fmt: any) => {
          const mimeType = fmt.mime_type || "";
          return mimeType.includes("audio");
        });
        
        console.log(`Found ${audioFormats.length} audio formats`);
        console.log("DEBUG Audio formats:", audioFormats.map((fmt: any) => ({
          mime_type: fmt.mime_type,
          bitrate: fmt.bitrate,
          has_url: !!fmt.url,
        })));
        
        if (audioFormats.length === 0) {
          console.error("No audio formats found");
          return false;
        }
        
        // Sort by bitrate and pick the best
        selectedFormat = audioFormats.sort((a: any, b: any) => {
          const aBitrate = Number(a.bitrate) || 0;
          const bBitrate = Number(b.bitrate) || 0;
          return bBitrate - aBitrate;
        })[0];
        
        console.log("Selected audio format:", selectedFormat.mime_type);
      } else {
        // For video, get video formats with best resolution
        const videoFormats = formats.filter((fmt: any) => {
          const mimeType = fmt.mime_type || "";
          return mimeType.includes("video");
        });
        
        console.log(`Found ${videoFormats.length} video formats`);
        console.log("DEBUG Video formats:", videoFormats.map((fmt: any) => ({
          mime_type: fmt.mime_type,
          width: fmt.width,
          height: fmt.height,
          quality_label: fmt.quality_label,
          has_url: !!fmt.url,
        })));
        
        if (videoFormats.length === 0) {
          console.error("No video formats found");
          return false;
        }
        
        // Sort by resolution (prefer 720p or lower for compatibility)
        selectedFormat = videoFormats.sort((a: any, b: any) => {
          const aHeight = a.height || 0;
          const bHeight = b.height || 0;
          
          // Prefer heights between 360p and 720p
          const aScore = aHeight <= 720 && aHeight >= 360 ? aHeight : 0;
          const bScore = bHeight <= 720 && bHeight >= 360 ? bHeight : 0;
          
          if (aScore > 0 && bScore > 0) return bScore - aScore;
          if (aScore > 0) return -1;
          if (bScore > 0) return 1;
          return bHeight - aHeight;
        })[0];
        
        console.log("Selected video format:", selectedFormat.mime_type, `${selectedFormat.width}x${selectedFormat.height}`);
      }

      console.log("DEBUG selectedFormat:", {
        exists: !!selectedFormat,
        mime_type: selectedFormat?.mime_type,
        has_url: !!selectedFormat?.url,
        url_length: selectedFormat?.url?.length,
        has_decipher: !!selectedFormat?.decipher,
        bitrate: selectedFormat?.bitrate,
        width: selectedFormat?.width,
        height: selectedFormat?.height,
      });

      if (!selectedFormat) {
        console.error("No format selected");
        return false;
      }

      // Handle URL deciphering if needed
      let downloadUrl = selectedFormat.url;
      
      if (!downloadUrl) {
        console.log("DEBUG Format needs deciphering");
        
        // Try to decipher using the format's decipher method
        if (typeof selectedFormat.decipher === 'function') {
          console.log("DEBUG Calling format.decipher()");
          try {
            downloadUrl = await selectedFormat.decipher(videoInfo.player);
            console.log("DEBUG Deciphered URL:", {
              hasUrl: !!downloadUrl,
              urlLength: downloadUrl?.length,
            });
          } catch (decipherError) {
            console.error("DEBUG format.decipher() failed:", decipherError);
          }
        }
        
        // If still no URL, try using the format's decipher method with Innertube instance
        if (!downloadUrl && typeof selectedFormat.decipher === 'function') {
          console.log("DEBUG Trying decipher with null param");
          try {
            downloadUrl = await selectedFormat.decipher(null);
            console.log("DEBUG Deciphered URL (null param):", {
              hasUrl: !!downloadUrl,
              urlLength: downloadUrl?.length,
            });
          } catch (decipherError) {
            console.error("DEBUG decipher(null) failed:", decipherError);
          }
        }
        
        // Last resort: check if format has a signature_cipher we can manually decode
        if (!downloadUrl && (selectedFormat as any).signature_cipher) {
          console.log("DEBUG Format has signature_cipher, attempting manual decode");
          try {
            // Parse the signature cipher
            const cipherData = (selectedFormat as any).signature_cipher;
            console.log("DEBUG signature_cipher data:", typeof cipherData);
            
            // If player is available, try to use it
            if (videoInfo.player) {
              console.log("DEBUG Using player to decipher");
              const actions = videoInfo.player;
              
              // Try to get the URL from signature cipher
              if (cipherData.url) {
                downloadUrl = cipherData.url;
                console.log("DEBUG Got URL from signature_cipher.url");
              }
            }
          } catch (cipherError) {
            console.error("DEBUG Manual cipher decode failed:", cipherError);
          }
        }
      }

      if (!downloadUrl) {
        console.error("Selected format has no URL and could not be deciphered");
        console.error("DEBUG selectedFormat full object:", JSON.stringify(selectedFormat, null, 2));
        console.error("DEBUG Available properties:", Object.keys(selectedFormat));
        console.error("DEBUG videoInfo.player exists:", !!videoInfo.player);
        
        // Last resort: Try to use videoInfo.download() method if available
        if (typeof (videoInfo as any).download === 'function') {
          console.log("DEBUG Attempting to use videoInfo.download() as fallback");
          try {
            const title = sanitizeFilename((videoInfo.basic_info as any)?.title?.text || (videoInfo.basic_info as any)?.title?.runs?.[0]?.text || (videoInfo.basic_info as any)?.title || "video");
            const fileName = `${title}.${formatType === "mp3" ? "m4a" : "mp4"}`;
            const cacheFilePath = `${this.cachePath}${fileName}`;
            
            console.log("DEBUG Downloading using videoInfo.download() to:", cacheFilePath);
            
            const downloadOptions = {
              type: formatType === "mp3" ? "audio" : "video+audio",
              quality: selectedFormat.quality_label || "best",
              format: "mp4",
            };
            
            console.log("DEBUG download options:", downloadOptions);
            
            // Note: videoInfo.download() returns a stream
            // We'd need to pipe it to a file, but FileSystem.downloadAsync doesn't accept streams
            // This approach won't work in React Native without additional stream handling
            console.error("videoInfo.download() returns a stream which is not compatible with React Native FileSystem");
            
          } catch (downloadMethodError) {
            console.error("videoInfo.download() fallback also failed:", downloadMethodError);
          }
        }
        
        console.error("");
        console.error("===============================================");
        console.error("YOUTUBEI.JS DECIPHER NOT WORKING");
        console.error("===============================================");
        console.error("The youtubei.js library's decipher() method is not working properly");
        console.error("in React Native. This video requires URL deciphering to download.");
        console.error("");
        console.error("Possible solutions:");
        console.error("1. Use yt-dlp binary (requires native module) - RECOMMENDED");
        console.error("2. Use a proxy server that handles deciphering");
        console.error("3. Try a different youtubei.js version");
        console.error("4. Use ytdl-core library as fallback");
        console.error("===============================================");
        
        return false;
      }

      console.log("DEBUG Final download URL obtained:", {
        hasUrl: !!downloadUrl,
        urlLength: downloadUrl?.length,
        urlStart: downloadUrl?.substring(0, 100),
      });

      const title = sanitizeFilename((videoInfo.basic_info as any)?.title?.text || (videoInfo.basic_info as any)?.title?.runs?.[0]?.text || (videoInfo.basic_info as any)?.title || "video");
      
      console.log("DEBUG title extracted:", title);
      
      // Extract file extension from mime type or use default
      let extension = "mp4";
      if (selectedFormat.mime_type) {
        // mime_type is like "video/mp4" or "audio/mp4"
        const parts = selectedFormat.mime_type.split("/");
        if (parts.length > 1) {
          const mimeSubtype = parts[1];
          // Handle cases like "audio/mp4", "video/mp4", "audio/webm", etc.
          if (mimeSubtype.includes("webm")) {
            extension = formatType === "mp3" ? "webm" : "webm";
          } else if (mimeSubtype.includes("mp4")) {
            extension = formatType === "mp3" ? "m4a" : "mp4";
          } else {
            extension = mimeSubtype.split(";")[0].trim() || extension;
          }
        }
      } else {
        extension = formatType === "mp3" ? "m4a" : "mp4";
      }

      console.log("DEBUG extension determined:", extension);

      const fileName = `${title}.${extension}`;
      const cacheFilePath = `${this.cachePath}${fileName}`;

      console.log("DEBUG file paths:", {
        fileName,
        cacheFilePath,
        cachePath: this.cachePath,
      });

      try {
        const cacheDirInfo = await FileSystem.getInfoAsync(this.cachePath);
        console.log("cacheDirInfo:", { exists: cacheDirInfo.exists, isDirectory: cacheDirInfo.isDirectory, uri: this.cachePath });
      } catch (e) {
        console.error("CRITICAL: Cache directory not accessible:", e, "path:", this.cachePath);
        throw new Error(`Cache directory not accessible: ${e}`);
      }

      console.log("download target", { fileName, cacheFilePath });

      // Download the file
      console.log("Starting download from streaming URL...");
      console.log("DEBUG download URL info:", {
        hasUrl: !!downloadUrl,
        urlLength: downloadUrl?.length,
        urlStart: downloadUrl?.substring(0, 100),
        urlProtocol: downloadUrl?.split("://")[0],
      });
      
      const downloadCallback = (downloadProgress: any) => {
        if (progressCallback && downloadProgress.totalBytesExpectedToWrite > 0) {
          const progress = (downloadProgress.totalBytesWritten / downloadProgress.totalBytesExpectedToWrite) * 100;
          progressCallback(progress);
        }
      };

      const resumable = FileSystem.createDownloadResumable(
        downloadUrl,
        cacheFilePath,
        {},
        downloadCallback
      );

      const downloadPromise = resumable.downloadAsync();
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error("Download timeout after 300s")), 300000)
      );

      let downloadResult;
      try {
        downloadResult = await Promise.race([downloadPromise, timeoutPromise]);
        console.log("downloadAsync succeeded:", { uri: (downloadResult as any)?.uri, status: (downloadResult as any)?.status });
      } catch (downloadErr) {
        console.error("downloadAsync failed or timed out:", downloadErr);
        try {
          const info = await FileSystem.getInfoAsync(cacheFilePath);
          console.log("Partial file exists after failed download:", { exists: info.exists, size: info.exists ? (info as any).size : undefined });
        } catch (infoErr) {
          console.warn("Failed to stat cacheFilePath after download error", infoErr);
        }
        throw downloadErr;
      }

      const finalPath = await this.moveFileToFinalDestination(cacheFilePath, fileName, selectedFormat.mime_type);

      console.log("downloadVideo finalized", { finalPath });

      if (completeCallback) {
        completeCallback(finalPath);
      }
      return true;
    } catch (error) {
      console.error("downloadVideo failed with exception:", error);
      console.error("Error details:", { 
        message: (error as any)?.message, 
        code: (error as any)?.code,
        name: (error as any)?.name,
        stack: (error as any)?.stack,
      });
      console.error("Full error object:", JSON.stringify(error, null, 2));
      return false;
    }
  }
}
