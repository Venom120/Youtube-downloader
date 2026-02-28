import React from "react";
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  FlatList,
  Linking,
  Alert,
} from "react-native";
import * as FileSystemLegacy from 'expo-file-system/legacy';
import * as IntentLauncher from 'expo-intent-launcher';
import { SafeAreaView, SafeAreaProvider } from "react-native-safe-area-context";
import { DownloadTask } from "../controllers/downloadController";

interface DownloadsListProps {
  visible: boolean;
  downloads: DownloadTask[];
  downloadPath: string;
  onClose: () => void;
  onPauseResume: (downloadId: string) => void;
  onCancel: (downloadId: string) => void;
}

export const DownloadsList: React.FC<DownloadsListProps> = ({
  visible,
  downloads,
  downloadPath,
  onClose,
  onPauseResume,
  onCancel,
}) => {
  const handleOpenFolder = async () => {
    try {
      if (!downloadPath) return;

      // 1. If we are using a SAF directory (content://), open it directly
      // Guard: strip any accidental 'SAF: ' prefix userspace code might add
      const rawPath = downloadPath.startsWith('SAF:') ? downloadPath.replace(/^SAF:\s*/i, '') : downloadPath;
      if (rawPath.startsWith('content://')) {
        try {
          await IntentLauncher.startActivityAsync('android.intent.action.VIEW', {
            data: rawPath,
            flags: 1, // FLAG_GRANT_READ_URI_PERMISSION
          });
          return;
        } catch (e) {
          console.warn('Failed to open SAF directory', e);
        }
      }

      // 2. For legacy paths, ensure proper file:// format
      const folderUri = downloadPath.startsWith("file://") ? downloadPath : `file://${downloadPath}`;

      try {
        // Attempt to convert to a content:// URI
        const contentUri = await FileSystemLegacy.getContentUriAsync(folderUri);
        await Linking.openURL(contentUri);
        return;
      } catch (e) {
        console.warn('getContentUriAsync failed, avoiding Intent crash', e);
      }

      // 3. Fallback: Open the generic Android File Manager without passing the strict file:// URI
      try {
        await IntentLauncher.startActivityAsync('android.intent.action.VIEW', { 
           type: '*/*', // Generic type to prompt file explorers
           flags: 1 
        });
      } catch (err) {
        console.error('Could not open file manager:', err);
        Alert.alert('Open folder failed', 'Cannot open the Downloads folder from the app. Please open your file manager manually.');
      }
    } catch (error) {
      console.error("Could not open folder:", error);
    }
  };
  const getStatusColor = (status: string): string => {
    switch (status) {
      case "downloading":
        return "#4CAF50"; // Green
      case "paused":
        return "#FF9800"; // Orange
      case "completed":
        return "#4CAF50"; // Green
      case "error":
        return "#F44336"; // Red
      case "canceled":
        return "#757575"; // Gray
      default:
        return "#2196F3"; // Blue
    }
  };

  const getStatusText = (status: string): string => {
    switch (status) {
      case "queued":
        return "Queued";
      case "downloading":
        return "Downloading";
      case "paused":
        return "Paused";
      case "completed":
        return "Completed";
      case "error":
        return "Error";
      case "canceled":
        return "Canceled";
      default:
        return "Unknown";
    }
  };

  const renderDownloadItem = (item: DownloadTask) => {
    const isActive = ["queued", "downloading", "paused"].includes(item.status);
    const isPaused = item.status === "paused";
    const canInteract = ["downloading", "paused", "queued"].includes(
      item.status
    );

    return (
      <View key={item.downloadId} style={styles.downloadItem}>
        <View style={styles.itemHeader}>
          <Text style={styles.videoTitle} numberOfLines={2}>
            {item.video.title.length > 50
              ? `${item.video.title.substring(0, 47)}...`
              : item.video.title}
          </Text>
          <View style={styles.statusBadge}>
            <View
              style={[
                styles.statusDot,
                { backgroundColor: getStatusColor(item.status) },
              ]}
            />
            <Text style={styles.statusText}>{getStatusText(item.status)}</Text>
          </View>
        </View>

        <View style={styles.metaRow}>
          <Text style={styles.metaText}>
            {item.formatType.toUpperCase()} • {Math.round(item.progress)}%
          </Text>
        </View>

        <View style={styles.progressBarContainer}>
          <View
            style={[
              styles.progressBar,
              {
                width: `${Math.min(item.progress, 100)}%`,
                backgroundColor: getStatusColor(item.status),
              },
            ]}
          />
        </View>

        {isActive && (
          <View style={styles.actionsRow}>
            {canInteract && (
              <TouchableOpacity
                style={[
                  styles.actionButton,
                  isPaused
                    ? styles.resumeButton
                    : styles.pauseButton,
                ]}
                onPress={() => onPauseResume(item.downloadId)}
              >
                <Text style={styles.actionButtonText}>
                  {isPaused ? "Resume" : "Pause"}
                </Text>
              </TouchableOpacity>
            )}
            {canInteract && (
              <TouchableOpacity
                style={[styles.actionButton, styles.cancelButton]}
                onPress={() => onCancel(item.downloadId)}
              >
                <Text style={styles.actionButtonText}>Cancel</Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        {item.error && (
          <Text style={styles.errorText}>{item.error}</Text>
        )}
      </View>
    );
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={false}
      onRequestClose={onClose}
    >
      <SafeAreaProvider>
        <SafeAreaView style={styles.container}>
            <View style={styles.header}>
            <Text style={styles.headerTitle}>
                Downloads ({downloads.length})
            </Text>
            <View style={styles.headerButtons}>
                <TouchableOpacity
                onPress={handleOpenFolder}
                style={styles.openFolderButton}
                >
                <Text style={styles.buttonText}>📁</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={onClose} style={styles.closeButton}>
                <Text style={styles.closeButtonText}>✕</Text>
                </TouchableOpacity>
            </View>
            </View>

            {downloads.length === 0 ? (
            <View style={styles.emptyContainer}>
                <Text style={styles.emptyText}>No downloads</Text>
            </View>
            ) : (
            <FlatList
                data={downloads}
                keyExtractor={(item) => item.downloadId}
                renderItem={({ item }) => renderDownloadItem(item)}
                contentContainerStyle={styles.listContent}
                scrollEnabled={true}
            />
            )}
        </SafeAreaView>
      </SafeAreaProvider>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f0f0f",
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#333333",
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#ffffff",
  },
  headerButtons: {
    flexDirection: "row",
    gap: 12,
    alignItems: "center",
  },
  openFolderButton: {
    padding: 8,
    backgroundColor: "#333333",
    borderRadius: 24,
    textAlignVertical: "center",
  },
  buttonText: {
    fontSize: 24,
    alignSelf: "center",
  },
  closeButton: {
    padding: 5,
    backgroundColor: "#333333",
    borderRadius: 24,
    height: 42,
    width: 42,
    textAlignVertical: "center",
  },
  closeButtonText: {
    fontSize: 24,
    color: "#ffffff",
    fontWeight: "bold",
    alignSelf: "center",
  },
  listContent: {
    padding: 8,
  },
  downloadItem: {
    backgroundColor: "#1a1a1a",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#333333",
    padding: 12,
    marginBottom: 12,
  },
  itemHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 8,
  },
  videoTitle: {
    flex: 1,
    fontSize: 14,
    fontWeight: "600",
    color: "#ffffff",
    marginRight: 8,
  },
  statusBadge: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#222222",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  statusText: {
    fontSize: 11,
    color: "#cccccc",
    fontWeight: "600",
  },
  metaRow: {
    marginBottom: 8,
  },
  metaText: {
    fontSize: 12,
    color: "#999999",
  },
  progressBarContainer: {
    height: 6,
    backgroundColor: "#333333",
    borderRadius: 3,
    overflow: "hidden",
    marginBottom: 8,
  },
  progressBar: {
    height: "100%",
    borderRadius: 3,
  },
  actionsRow: {
    flexDirection: "row",
    gap: 8,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    alignItems: "center",
    justifyContent: "center",
  },
  pauseButton: {
    backgroundColor: "#555555",
  },
  resumeButton: {
    backgroundColor: "#FF9800",
  },
  cancelButton: {
    backgroundColor: "#F44336",
  },
  actionButtonText: {
    color: "#ffffff",
    fontSize: 12,
    fontWeight: "600",
  },
  errorText: {
    fontSize: 12,
    color: "#F44336",
    marginTop: 8,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  emptyText: {
    fontSize: 16,
    color: "#999999",
  },
});
