import { StatusBar } from "expo-status-bar";
import * as FileSystem from "expo-file-system";
import * as MediaLibrary from "expo-media-library";
import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  Platform,
  PermissionsAndroid,
  Linking,
  Alert,
} from "react-native";
import { SafeAreaView, SafeAreaProvider } from "react-native-safe-area-context";
import * as IntentLauncher from 'expo-intent-launcher';
import * as Application from 'expo-application';
import * as FileSystemLegacy from 'expo-file-system/legacy';
import { DownloadController, DownloadTask } from "./src/controllers/downloadController";
import { SearchController } from "./src/controllers/searchController";
import { VideoInfo } from "./src/models/videoModel";
import { VideoCard } from "./src/views/VideoCard";
import { DownloadsList } from "./src/views/DownloadsList";

const isUrl = (value: string): boolean => /^https?:\/\//i.test(value.trim());
const isPlaylistUrl = (value: string): boolean => /[?&]list=/.test(value);

export default function App() {
  const [query, setQuery] = useState("");
  const [videos, setVideos] = useState<VideoInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [downloadPath, setDownloadPath] = useState<string>("");
  const [cachePath, setCachePath] = useState<string>("");
  const [downloadProgress, setDownloadProgress] = useState<Record<string, number>>({});
  const [downloads, setDownloads] = useState<DownloadTask[]>([]);
  const [showDownloadsModal, setShowDownloadsModal] = useState(false);
  const [isReady, setIsReady] = useState(false);

  const searchController = useMemo(() => new SearchController(), []);
  const downloadControllerRef = useRef<DownloadController | null>(null);
  const downloadUpdateIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const requireExternalDownloadDir = false; // use media-library fallback when external storage isn't writable

  useEffect(() => {
    const initDownloadDir = async () => {
      try {
        // Request MediaLibrary permission (for media access) first
        const { status } = await MediaLibrary.requestPermissionsAsync();
        if (status !== "granted") {
          console.warn("Media library permission not granted:", status);
          setError(
            "Media library permission is recommended to save downloads. You can grant it in app settings."
          );
        }

        // Request Android file permissions when running on Android
        const ensureAndroidStorage = async (): Promise<boolean> => {
          if (Platform.OS !== "android") return true;
          try {
            const perms = await PermissionsAndroid.requestMultiple([
              PermissionsAndroid.PERMISSIONS.READ_EXTERNAL_STORAGE,
              PermissionsAndroid.PERMISSIONS.WRITE_EXTERNAL_STORAGE,
            ]);

            const write = perms[PermissionsAndroid.PERMISSIONS.WRITE_EXTERNAL_STORAGE];
            const read = perms[PermissionsAndroid.PERMISSIONS.READ_EXTERNAL_STORAGE];

            // On Android 11+ WRITE_EXTERNAL_STORAGE may not be sufficient due to scoped storage.
            if (Platform.Version >= 30) {
              // Prompt the user to grant "All files access" (MANAGE_EXTERNAL_STORAGE)
              return new Promise<boolean>((resolve) => {
                Alert.alert(
                  'Storage access required',
                  'To save files to the device Download folder, allow "All files access" for this app in settings.\n\nOpen settings now?',
                  [
                    {
                      text: 'Open Settings',
                      onPress: async () => {
                        try {
                          const action = 'android.settings.MANAGE_APP_ALL_FILES_ACCESS_PERMISSION';
                          const pkg = `package:${Application.applicationId}`;
                          await IntentLauncher.startActivityAsync(action, { data: pkg });
                        } catch (e) {
                          console.warn('Failed to open Manage All Files Access screen', e);
                          try {
                            Linking.openSettings();
                          } catch (e2) {
                            console.warn('Failed to open settings screen', e2);
                          }
                        }
                        // Give user time to toggle the permission and then retry externally
                        resolve(false);
                      },
                    },
                    {
                      text: 'Use app storage',
                      style: 'cancel',
                      onPress: () => resolve(false),
                    },
                  ],
                  { cancelable: false }
                );
              });
            }

            if (write === PermissionsAndroid.RESULTS.GRANTED) {
              return true;
            }

            setError("Storage permission denied. Cannot save to external Download folder.");
            return false;
          } catch (e) {
            console.warn("Error requesting Android storage permissions", e);
            return false;
          }
        };

        const hasStorage = await ensureAndroidStorage();

        let finalDownloadDir: FileSystem.Directory | null = null;
        let cacheDir: FileSystem.Directory | null = null;

        // Set up cache directory
        try {
          const appCacheDir = FileSystem.Paths.cache;
          cacheDir = new FileSystem.Directory(appCacheDir, "YTDownloader");
          if (!cacheDir.exists) {
            cacheDir.create({ intermediates: true, idempotent: true });
          }
          console.log("Cache directory ready:", cacheDir.uri);
          setCachePath(cacheDir.uri);
        } catch (cacheError) {
          console.error("Failed to create cache directory:", cacheError);
        }

        // Try to access Android's public Download folder
        try {
          // Detect external storage base path by probing common locations instead
          const probeBases = [
            "file:///storage/emulated/0",
            "file:///sdcard",
            "file:///mnt/sdcard",
            "file:///storage/sdcard0",
          ];

          let baseFound: string | null = null;
          for (const base of probeBases) {
            try {
              const info = await FileSystem.getInfoAsync(base);
              if (info.exists) {
                baseFound = base;
                break;
              }
            } catch (e) {
              // ignore
            }
          }

          if (baseFound) {
            const externalDownloadPath = `${baseFound}/Download/YTDownloader`;
            const externalDir = new FileSystem.Directory(externalDownloadPath);
            console.log("Attempting to access external Download folder:", externalDownloadPath);
            try {
              if (!externalDir.exists) {
                await externalDir.create({ intermediates: true, idempotent: true });
                console.log("Created external Download folder");
              } else {
                console.log("Using existing external Download folder");
              }
              finalDownloadDir = externalDir;
            } catch (createError) {
              console.warn("Cannot create external Download folder:", createError);
            }
          } else {
            console.log("No external storage base found; skipping external Download probe.");
          }
        } catch (externalError) {
          console.warn("Cannot access external storage:", externalError);
        }

        // If we couldn't create/use the external Download folder, prompt user to pick a directory via SAF
        let safDirectoryUri: string | null = null;
        if (!finalDownloadDir) {
          try {
            const { StorageAccessFramework } = FileSystemLegacy as any;
            // Try to target the native Downloads root if helper exists
            let initialUri: string | undefined = undefined;
            try {
              if (typeof StorageAccessFramework.getUriForDirectoryInRoot === 'function') {
                initialUri = StorageAccessFramework.getUriForDirectoryInRoot('Download');
              }
            } catch (e) {
              // ignore
            }

            const perms = await StorageAccessFramework.requestDirectoryPermissionsAsync(initialUri);
            if (perms.granted) {
              safDirectoryUri = perms.directoryUri;
              console.log('User selected SAF directory:', safDirectoryUri);
            } else {
              console.log('User did not grant SAF directory access');
            }
          } catch (e) {
            console.warn('SAF directory selection failed or not supported in this environment', e);
          }
        }

        // Fallback to app's document directory
        if (!finalDownloadDir && !requireExternalDownloadDir) {
          console.log("Falling back to app document directory");
          const documentDir = FileSystem.Paths.document;
          finalDownloadDir = new FileSystem.Directory(documentDir, "YTDownloader");
          
          try {
            if (!finalDownloadDir.exists) {
              finalDownloadDir.create({ intermediates: true, idempotent: true });
            }
            console.log("YTDownloader folder ready in document directory");
          } catch (createError) {
            console.log("Directory creation note:", createError);
          }
        }

        if (!cacheDir || !cacheDir.uri) {
          console.error("No cache directory available");
          setError("File system cache not ready. Please try again.");
          return;
        }

        // If we have an external finalDownloadDir, use its URI. Otherwise fall back to media-library album.
        if (finalDownloadDir && finalDownloadDir.uri) {
          const path = finalDownloadDir.uri;
          console.log("Download directory ready:", path);
          setDownloadPath(path);
          downloadControllerRef.current = new DownloadController(path, cacheDir.uri);
        } else if (typeof safDirectoryUri === 'string' && safDirectoryUri) {
          // Use SAF directory picked by user
          console.log('Using SAF directory as final destination:', safDirectoryUri);
          setDownloadPath(`SAF: ${safDirectoryUri}`);
          downloadControllerRef.current = new DownloadController(safDirectoryUri, cacheDir.uri, true);
        } else {
          // Use media library fallback; show album name as download path
          const albumName = "YTDownloader";
          console.log("Using media-library album as final destination:", albumName);
          setDownloadPath(`Media Library / ${albumName}`);
          downloadControllerRef.current = new DownloadController("", cacheDir.uri);
        }
        setIsReady(true);
      } catch (err) {
        console.error("initDownloadDir failed:", err);
        setError(
          "Failed to initialize download directory. Build the APK for production use: `eas build` or `expo build`."
        );
      }
    };

    initDownloadDir();

    // Set up interval to refresh downloads list
    downloadUpdateIntervalRef.current = setInterval(() => {
      if (downloadControllerRef.current) {
        setDownloads([...downloadControllerRef.current.getAllDownloads()]);
      }
    }, 500);

    return () => {
      if (downloadUpdateIntervalRef.current) {
        clearInterval(downloadUpdateIntervalRef.current);
      }
    };
  }, []);

  const handleSearch = async () => {
    if (!query.trim()) {
      return;
    }

    setLoading(true);
    setError(null);
    setVideos([]);

    try {
      if (isUrl(query) && isPlaylistUrl(query)) {
        await searchController.getPlaylistVideos(
          query,
          (results) => setVideos(results),
          (err) => setError(err)
        );
      } else if (isUrl(query)) {
        await searchController.getVideoInfo(
          query,
          (info) => setVideos(info ? [info] : []),
          (err) => setError(err)
        );
      } else {
        await searchController.searchVideos(
          query,
          20,
          (result) => setVideos(result.videos),
          (err) => setError(err)
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const startDownload = async (video: VideoInfo, formatType: "mp4" | "mp3") => {
    if (!isReady || !downloadControllerRef.current) {
      setError("Download system is initializing. Please wait...");
      return;
    }

    const key = `${video.videoId}-${formatType}`;
    setDownloadProgress((prev) => ({ ...prev, [key]: 0 }));

    await downloadControllerRef.current.downloadVideo(
      video,
      formatType,
      (progress) => {
        setDownloadProgress((prev) => ({
          ...prev,
          [key]: progress,
        }));
        // Update downloads list
        if (downloadControllerRef.current) {
          setDownloads([...downloadControllerRef.current.getAllDownloads()]);
        }
      },
      () => {
        setDownloadProgress((prev) => ({
          ...prev,
          [key]: 100,
        }));
        // Update downloads list
        if (downloadControllerRef.current) {
          setDownloads([...downloadControllerRef.current.getAllDownloads()]);
        }
      },
      (err) => {
        setError(err);
        // Update downloads list
        if (downloadControllerRef.current) {
          setDownloads([...downloadControllerRef.current.getAllDownloads()]);
        }
      }
    );

    // Update downloads list
    if (downloadControllerRef.current) {
      setDownloads([...downloadControllerRef.current.getAllDownloads()]);
    }
  };

  const handlePauseResume = (downloadId: string) => {
    if (!downloadControllerRef.current) return;

    const task = downloadControllerRef.current.getDownload(downloadId);
    if (!task) return;

    if (task.status === "paused") {
      downloadControllerRef.current.resumeDownload(downloadId);
    } else {
      downloadControllerRef.current.pauseDownload(downloadId);
    }

    setDownloads([...downloadControllerRef.current.getAllDownloads()]);
  };

  const handleCancel = (downloadId: string) => {
    if (!downloadControllerRef.current) return;

    downloadControllerRef.current.cancelDownload(downloadId);
    setDownloads([...downloadControllerRef.current.getAllDownloads()]);
  };

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" />
        <View style={styles.header}>
          <View>
            <Text style={styles.title}>YT Downloader</Text>
            <Text style={styles.subtitle}>Search or paste a YouTube URL</Text>
          </View>
          <TouchableOpacity
            style={styles.downloadsButton}
            onPress={() => setShowDownloadsModal(true)}
          >
            <Text style={styles.downloadsButtonText}>
              ⬇ {downloads.length}
            </Text>
          </TouchableOpacity>
        </View>
        <View style={styles.searchRow}>
          <TextInput
            value={query}
            onChangeText={setQuery}
            placeholder="Search videos or paste URL"
            placeholderTextColor="#6b6b6b"
            style={styles.searchInput}
            editable={!loading}
          />
          <TouchableOpacity style={styles.searchButton} onPress={handleSearch} disabled={loading}>
            <Text style={styles.searchButtonText}>Search</Text>
          </TouchableOpacity>
        </View>
        {downloadPath ? <Text style={styles.downloadPath}>Downloads: {downloadPath}</Text> : null}
        {cachePath ? <Text style={styles.downloadPath}>Cache: {cachePath}</Text> : null}
        {error ? <Text style={styles.errorText}>{error}</Text> : null}
        {!isReady && downloadPath === "" ? (
          <View style={styles.loadingRow}>
            <ActivityIndicator color="#ffffff" />
            <Text style={styles.loadingText}>Initializing...</Text>
          </View>
        ) : null}
        {loading ? (
          <View style={styles.loadingRow}>
            <ActivityIndicator color="#ffffff" />
            <Text style={styles.loadingText}>Loading results...</Text>
          </View>
        ) : null}
        <ScrollView contentContainerStyle={styles.results}>
          {videos.map((video) => {
            const mp4Key = `${video.videoId}-mp4`;
            const mp3Key = `${video.videoId}-mp3`;
            const progress = downloadProgress[mp4Key] ?? downloadProgress[mp3Key];
            const disabled = !isReady || (progress !== undefined && progress < 100);
            return (
              <VideoCard
                key={video.videoId}
                video={video}
                progress={progress}
                disabled={disabled}
                onMp4Press={() => startDownload(video, "mp4")}
                onMp3Press={() => startDownload(video, "mp3")}
              />
            );
          })}
          {!loading && videos.length === 0 ? (
            <Text style={styles.emptyText}>No results yet. Try a search!</Text>
          ) : null}
        </ScrollView>
        <DownloadsList
          visible={showDownloadsModal}
          downloads={downloads}
          downloadPath={downloadPath}
          onClose={() => setShowDownloadsModal(false)}
          onPauseResume={handlePauseResume}
          onCancel={handleCancel}
        />
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f0f0f",
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 8,
  },
  title: {
    color: "#fff",
    fontSize: 26,
    fontWeight: "700",
  },
  subtitle: {
    color: "#9b9b9b",
    marginTop: 4,
  },
  downloadsButton: {
    backgroundColor: "#0066cc",
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    justifyContent: "center",
    alignItems: "center",
    minWidth: 60,
  },
  downloadsButtonText: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "600",
  },
  searchRow: {
    flexDirection: "row",
    gap: 12,
    paddingHorizontal: 20,
    marginTop: 12,
  },
  searchInput: {
    flex: 1,
    backgroundColor: "#1f1f1f",
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    color: "#fff",
  },
  searchButton: {
    backgroundColor: "#d91f1f",
    paddingHorizontal: 18,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  searchButtonText: {
    color: "#fff",
    fontWeight: "600",
  },
  downloadPath: {
    color: "#6b6b6b",
    paddingHorizontal: 20,
    marginTop: 8,
    fontSize: 12,
  },
  errorText: {
    color: "#f87171",
    paddingHorizontal: 20,
    marginTop: 8,
  },
  loadingRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 20,
    marginTop: 16,
  },
  loadingText: {
    color: "#d4d4d4",
  },
  results: {
    paddingHorizontal: 20,
    paddingVertical: 24,
  },
  emptyText: {
    color: "#6b6b6b",
    textAlign: "center",
    marginTop: 48,
  },
});
