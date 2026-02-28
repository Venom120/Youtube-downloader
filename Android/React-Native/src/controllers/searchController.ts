import { SearchResult, VideoInfo } from "../models/videoModel";
import { YTDLPWrapper } from "../services/ytdlWrapper-server";

export class SearchController {
  private ytdlp: YTDLPWrapper;
  public currentSearchResult: SearchResult | null = null;
  public currentPlaylistVideos: VideoInfo[] = [];

  constructor() {
    this.ytdlp = new YTDLPWrapper();
  }

  async searchVideos(
    query: string,
    maxResults: number = 20,
    callback?: (result: SearchResult) => void,
    errorCallback?: (error: string) => void
  ): Promise<void> {
    try {
      const result = await this.ytdlp.searchVideos(query, maxResults);
      this.currentSearchResult = result;
      callback?.(result);
    } catch (error) {
      errorCallback?.(String(error));
    }
  }

  async getVideoInfo(
    url: string,
    callback?: (video: VideoInfo | null) => void,
    errorCallback?: (error: string) => void
  ): Promise<void> {
    try {
      const info = await this.ytdlp.getVideoInfo(url);
      callback?.(info);
    } catch (error) {
      errorCallback?.(String(error));
    }
  }

  async getPlaylistVideos(
    url: string,
    callback?: (videos: VideoInfo[]) => void,
    errorCallback?: (error: string) => void
  ): Promise<void> {
    try {
      const videos = await this.ytdlp.getPlaylistVideos(url);
      this.currentPlaylistVideos = videos;
      callback?.(videos);
    } catch (error) {
      errorCallback?.(String(error));
    }
  }
}
