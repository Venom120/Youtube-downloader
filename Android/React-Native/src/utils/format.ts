export const formatDuration = (duration: number): string => {
  if (duration < 0) {
    return "Unknown";
  }

  const hours = Math.floor(duration / 3600);
  const minutes = Math.floor((duration % 3600) / 60);
  const seconds = Math.floor(duration % 60);

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  }

  return `${minutes}:${String(seconds).padStart(2, "0")}`;
};

export const formatViews = (viewCount?: number | null): string => {
  if (viewCount === null || viewCount === undefined) {
    return "Unknown";
  }

  if (viewCount >= 1_000_000) {
    return `${(viewCount / 1_000_000).toFixed(1)}M`;
  }

  if (viewCount >= 1_000) {
    return `${(viewCount / 1_000).toFixed(1)}K`;
  }

  return String(viewCount);
};
