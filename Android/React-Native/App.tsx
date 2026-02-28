import { StatusBar } from "expo-status-bar";
import * as FileSystem from "expo-file-system";
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
import AsyncStorage from '@react-native-async-storage/async-storage';
import { DownloadController, DownloadTask } from "./src/controllers/downloadController";
import { SearchController } from "./src/controllers/searchController";
import { VideoInfo } from "./src/models/videoModel";
import { VideoCard } from "./src/views/VideoCard";
import { DownloadsList } from "./src/views/DownloadsList";

const isUrl = (value: string): boolean => /^https?:\/\//i.test(value.trim());
const isPlaylistUrl = (value: string): boolean => /[?&]list=/.test(value);

const SAF_STORAGE_KEY = '@ytdownloader_saf_uri';

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

  useEffect(() => {
    const initDownloadDir = async () => {
      try {
        // Request Android file permissions when running on Android
        const ensureAndroidStorage = async (): Promise<boolean> => {
          if (Platform.OS !== "android") return true;
          try {
            const perms = await PermissionsAndroid.requestMultiple([
              PermissionsAndroid.PERMISSIONS.READ_EXTERNAL_STORAGE,
              PermissionsAndroid.PERMISSIONS.WRITE_EXTERNAL_STORAGE,
            ]);

            const write = perms[PermissionsAndroid.PERMISSIONS.WRITE_EXTERNAL_STORAGE];

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

        // Try to load stored SAF directory URI from AsyncStorage
        let safDirectoryUri: string | null = null;
        try {
          const storedUri = await AsyncStorage.getItem(SAF_STORAGE_KEY);
          if (storedUri) {
            console.log('Found stored SAF URI:', storedUri);
            // Verify the stored URI still has access
            try {
              const { StorageAccessFramework } = FileSystemLegacy as any;
              const files = await StorageAccessFramework.readDirectoryAsync(storedUri);
              console.log('Stored SAF URI is valid, has access to', files.length, 'items');
              safDirectoryUri = storedUri;
            } catch (verifyErr) {
              console.warn('Stored SAF URI no longer accessible, will prompt user:', verifyErr);
              // Clear invalid stored URI
              await AsyncStorage.removeItem(SAF_STORAGE_KEY);
            }
          }
        } catch (storageErr) {
          console.warn('Failed to load stored SAF URI:', storageErr);
        }

        // Prompt user to pick a directory via SAF if no valid stored URI
        if (!safDirectoryUri && !finalDownloadDir) {
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
              // Save the selected URI to AsyncStorage
              try {
                await AsyncStorage.setItem(SAF_STORAGE_KEY, safDirectoryUri!);
                console.log('Saved SAF URI to storage');
              } catch (saveErr) {
                console.warn('Failed to save SAF URI:', saveErr);
              }
            } else {
              console.log('User did not grant SAF directory access');
            }
          } catch (e) {
            console.warn('SAF directory selection failed or not supported in this environment', e);
          }
        }

        if (!cacheDir || !cacheDir.uri) {
          console.error("No cache directory available");
          setError("File system cache not ready. Please try again.");
          return;
        }

        // SAF-only flow: require the user to select a directory via SAF
        if (typeof safDirectoryUri === 'string' && safDirectoryUri) {
          console.log('Using SAF directory as final destination:', safDirectoryUri);
          // Store the raw SAF URI so downstream logic can detect content:// correctly
          setDownloadPath(safDirectoryUri);
          downloadControllerRef.current = new DownloadController(safDirectoryUri, cacheDir.uri, true);
          setIsReady(true);
        } else {
          console.error('No SAF directory selected — downloads disabled.');
          setError('Please choose a destination folder when prompted so downloads can be saved (SAF).');
          return;
        }
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

  const handleChangeSafDirectory = async () => {
    try {
      const { StorageAccessFramework } = FileSystemLegacy as any;
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
        const newSafUri = perms.directoryUri;
        console.log('User selected new SAF directory:', newSafUri);
        
        // Save to AsyncStorage
        await AsyncStorage.setItem(SAF_STORAGE_KEY, newSafUri);
        console.log('Saved new SAF URI to storage');
        
        // Update state and recreate download controller
        setDownloadPath(newSafUri);
        if (cachePath) {
          downloadControllerRef.current = new DownloadController(newSafUri, cachePath, true);
          setIsReady(true);
          setError(null);
          Alert.alert('Success', 'Download folder updated successfully');
        }
      } else {
        console.log('User cancelled SAF directory selection');
      }
    } catch (e) {
      console.error('Failed to change SAF directory:', e);
      Alert.alert('Error', 'Failed to change download folder');
    }
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
          <View style={styles.headerButtons}>
            <TouchableOpacity
              style={styles.folderButton}
              onPress={handleChangeSafDirectory}
            >
              <Text style={styles.downloadsButtonText}>📁</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.downloadsButton}
              onPress={() => setShowDownloadsModal(true)}
            >
              <Text style={styles.downloadsButtonText}>
                ⬇ {downloads.length}
              </Text>
            </TouchableOpacity>
          </View>
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
  headerButtons: {
    flexDirection: "row",
    gap: 8,
  },
  folderButton: {
    backgroundColor: "#cc6600",
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    justifyContent: "center",
    alignItems: "center",
    minWidth: 50,
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
