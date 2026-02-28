import React from "react";
import { Image, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { VideoInfo } from "../models/videoModel";
import { formatDuration, formatViews } from "../utils/format";

type Props = {
  video: VideoInfo;
  onMp4Press: (video: VideoInfo) => void;
  onMp3Press: (video: VideoInfo) => void;
  progress?: number;
  disabled?: boolean;
};

export const VideoCard: React.FC<Props> = ({
  video,
  onMp4Press,
  onMp3Press,
  progress,
  disabled,
}) => {
  const infoParts = [video.channel];
  if (video.viewCount) {
    infoParts.push(`${formatViews(video.viewCount)}`);
  }

  const resolvedProgress = progress;

  return (
    <View style={styles.card}>
      <View style={styles.thumbnailWrapper}>
        {video.thumbnailUrl ? (
          <Image 
            source={{ uri: video.thumbnailUrl }} 
            style={styles.thumbnail}
          />
        ) : (
          <View style={styles.thumbnailPlaceholder} />
        )}
        <View style={styles.badge}>
          <Text style={styles.badgeText}>
            {video.isPlaylist ? `\u{1F4D1} ${video.playlistCount || 0}` : formatDuration(video.duration)}
          </Text>
        </View>
      </View>
      <View style={styles.content}>
        <Text style={styles.title} numberOfLines={2}>
          {video.title}
        </Text>
        <Text style={styles.meta} numberOfLines={1}>
          {infoParts.join(" \u2022 ")}
        </Text>
        <View style={styles.actions}>
          <TouchableOpacity
            style={[styles.button, styles.mp4Button, disabled && styles.buttonDisabled]}
            onPress={() => onMp4Press(video)}
            disabled={disabled}
          >
            <Text style={styles.buttonText}>MP4</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.button, styles.mp3Button, disabled && styles.buttonDisabled]}
            onPress={() => onMp3Press(video)}
            disabled={disabled}
          >
            <Text style={styles.buttonText}>MP3</Text>
          </TouchableOpacity>
        </View>
        {resolvedProgress !== undefined ? (
          <View style={styles.progressRow}>
            <View style={styles.progressTrack}>
              <View style={[styles.progressFill, { width: `${Math.min(Math.max(resolvedProgress, 0), 100)}%` }]} />
            </View>
            <Text style={styles.progressText}>{Math.round(resolvedProgress || 0)}%</Text>
          </View>
        ) : null}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#161616",
    borderRadius: 16,
    marginBottom: 16,
    overflow: "hidden",
  },
  thumbnailWrapper: {
    position: "relative",
    height: 180,
    backgroundColor: "#2a2a2a",
  },
  thumbnail: {
    width: "100%",
    height: "100%",
  },
  thumbnailPlaceholder: {
    flex: 1,
    backgroundColor: "#2a2a2a",
  },
  badge: {
    position: "absolute",
    right: 12,
    bottom: 12,
    backgroundColor: "rgba(0,0,0,0.7)",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  badgeText: {
    color: "#fff",
    fontSize: 12,
    fontWeight: "600",
  },
  content: {
    padding: 16,
  },
  title: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
  meta: {
    color: "#b3b3b3",
    marginTop: 6,
  },
  actions: {
    flexDirection: "row",
    gap: 12,
    marginTop: 12,
  },
  button: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 10,
    alignItems: "center",
  },
  mp4Button: {
    backgroundColor: "#0066cc",
  },
  mp3Button: {
    backgroundColor: "#cc2f2f",
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: "#fff",
    fontWeight: "600",
  },
  progressRow: {
    marginTop: 12,
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  progressTrack: {
    flex: 1,
    height: 6,
    backgroundColor: "#2b2b2b",
    borderRadius: 999,
    overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    backgroundColor: "#16a34a",
  },
  progressText: {
    color: "#b3b3b3",
    fontSize: 12,
  },
});
