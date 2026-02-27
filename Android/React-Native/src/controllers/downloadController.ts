import { VideoInfo } from "../models/videoModel";
import { YTDLPWrapper } from "../services/ytdlpWrapper";

export type DownloadTask = {
  downloadId: string;
  video: VideoInfo;
  formatType: "mp4" | "mp3";
  status: "queued" | "downloading" | "paused" | "completed" | "canceled" | "error";
  progress: number;
  error?: string;
  pauseFlag?: boolean;
  cancelFlag?: boolean;
};

const createId = (): string => Math.random().toString(36).slice(2, 10);

export class DownloadController {
  private ytdlp: YTDLPWrapper;
  public allDownloads = new Map<string, DownloadTask>();
  public downloadHistory: DownloadTask[] = [];

  constructor(downloadPath: string, cachePath: string, downloadPathIsSaf?: boolean) {
    // downloadPathIsSaf indicates that downloadPath is a SAF directory URI
    this.ytdlp = new YTDLPWrapper(cachePath, downloadPath, downloadPathIsSaf);
  }

  async downloadVideo(
    video: VideoInfo,
    formatType: "mp4" | "mp3" = "mp4",
    progressCallback?: (progress: number) => void,
    completeCallback?: (filename: string) => void,
    errorCallback?: (error: string) => void
  ): Promise<string> {
    const downloadId = createId();
    const task: DownloadTask = {
      downloadId,
      video,
      formatType,
      status: "queued",
      progress: 0,
      pauseFlag: false,
      cancelFlag: false,
    };

    this.allDownloads.set(downloadId, task);

    task.status = "downloading";

    const success = await this.ytdlp.downloadVideo(
      video.url,
      formatType,
      (progress) => {
        task.progress = progress;
        progressCallback?.(progress);
      },
      (filename) => {
        if (!task.cancelFlag) {
          task.progress = 100;
          task.status = "completed";
          completeCallback?.(filename);
        }
      }
    );

    if (!success) {
      if (task.cancelFlag) {
        task.status = "canceled";
        task.error = "Canceled";
      } else {
        task.status = "error";
        task.error = "Download failed";
        errorCallback?.(task.error);
      }
    }

    this.downloadHistory.push(task);
    return downloadId;
  }

  pauseDownload(downloadId: string): boolean {
    const task = this.allDownloads.get(downloadId);
    if (!task || !["downloading", "queued"].includes(task.status)) {
      return false;
    }
    task.pauseFlag = true;
    task.status = "paused";
    return true;
  }

  resumeDownload(downloadId: string): boolean {
    const task = this.allDownloads.get(downloadId);
    if (!task || task.status !== "paused") {
      return false;
    }
    task.pauseFlag = false;
    task.status = "downloading";
    return true;
  }

  cancelDownload(downloadId: string): boolean {
    const task = this.allDownloads.get(downloadId);
    if (!task || ["completed", "canceled", "error"].includes(task.status)) {
      return false;
    }
    task.cancelFlag = true;
    task.pauseFlag = false;
    task.status = "canceled";
    task.error = "Canceled";
    return true;
  }

  getDownload(downloadId: string): DownloadTask | undefined {
    return this.allDownloads.get(downloadId);
  }

  getActiveDownloads(): DownloadTask[] {
    return Array.from(this.allDownloads.values()).filter(
      (task) => !["completed", "canceled", "error"].includes(task.status)
    );
  }

  getAllDownloads(): DownloadTask[] {
    return Array.from(this.allDownloads.values());
  }
}
