export type VideoInfo = {
  videoId: string;
  title: string;
  thumbnailUrl: string;
  duration: number;
  channel: string;
  viewCount?: number | null;
  uploadDate?: string | null;
  url: string;
  isPlaylist: boolean;
  playlistCount?: number | null;
};

export type SearchResult = {
  videos: VideoInfo[];
  query: string;
  page: number;
  hasMore: boolean;
};
