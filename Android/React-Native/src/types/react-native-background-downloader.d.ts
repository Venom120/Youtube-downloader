declare module '@kesha-antonov/react-native-background-downloader' {
  export interface DownloadTask {
    id: string;
    url: string;
    destination: string;
    
    begin(callback: (expectedBytes: number) => void): DownloadTask;
    progress(callback: (percent: number, bytesWritten: number, bytesTotal: number) => void): DownloadTask;
    done(callback: () => void): DownloadTask;
    error(callback: (error: string) => void): DownloadTask;
    
    pause(): void;
    resume(): void;
    stop(): void;
  }

  export interface DownloadOptions {
    id: string;
    url: string;
    destination: string;
  }

  const RNBackgroundDownloader: {
    download(options: DownloadOptions): DownloadTask;
    checkForExistingDownloads(): Promise<DownloadTask[]>;
  };

  export default RNBackgroundDownloader;
}
