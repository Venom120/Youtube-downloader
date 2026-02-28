export const parseViewCount = (viewCountText: string): number | undefined => {
  if (!viewCountText) {
    return undefined;
  }

  // Remove "views" and extra whitespace
  let text = viewCountText.toLowerCase().replace(/\s*views?\s*$/i, "").trim();

  // Match number with optional decimal and suffix (K, M, B)
  const match = text.match(/^([\d.]+)\s*([kmb])?$/i);
  if (!match) {
    return undefined;
  }

  const number = parseFloat(match[1]);
  const suffix = (match[2] || "").toUpperCase();

  switch (suffix) {
    case "K":
      return Math.round(number * 1000);
    case "M":
      return Math.round(number * 1000000);
    case "B":
      return Math.round(number * 1000000000);
    default:
      return Math.round(number);
  }
};

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

  if (viewCount >= 1000000) {
    return `${(viewCount / 1000000).toFixed(1)}M`;
  }

  if (viewCount >= 1000) {
    return `${(viewCount / 1000).toFixed(1)}K`;
  }

  return String(viewCount);
};
