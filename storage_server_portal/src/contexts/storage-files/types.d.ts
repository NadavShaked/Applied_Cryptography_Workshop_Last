export interface ErrorStatus {
  statusCode: number;
  message: string;
}

export interface StorageFilesContextValue {
  storageFiles: StorageFile[];
  getStorageFilesError: ErrorStatus | null;
  getStorageFilesLoadingState: LoadingState;
  deleteStorageFile: (fileName: string) => void;
}
