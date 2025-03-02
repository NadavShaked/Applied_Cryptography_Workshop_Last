'use client';

import * as React from 'react';
import { ReactNode, useEffect, useState } from 'react';

import { StorageFile } from '@/types/storage-files/storage-file';
import { LoadingState } from '@/lib/async-data/async-data.utils';
import { storageFilesClient } from '@/lib/clients/products/client';
import { logger } from '@/lib/default-logger';

import { type StorageFilesContextValue } from './types';

export const StorageFilesContext = React.createContext<StorageFilesContextValue | undefined>(undefined);

export interface StorageFilesProviderProps {
  children: ReactNode;
}

export const StorageFilesProvider: React.FC<StorageFilesProviderProps> = ({ children }) => {
  const [state, setState] = useState<StorageFilesContextValue>({
    storageFiles: [],
    getStorageFilesError: null,
    getStorageFilesLoadingState: LoadingState.Idle,
    deleteStorageFile: async (fileName) => {
      await storageFilesClient.DeleteStorageFiles(fileName);
    },
  });

  useEffect(() => {
    const fetchData = async () => {
      setState((prev) => ({ ...prev, getStorageFilesLoadingState: LoadingState.Loading }));

      try {
        const { data, error } = await storageFilesClient.GetStorageFiles();

        const retVal: StorageFile[] = data ?? [];

        if (error) {
          logger.error(error.message);
          setState(() => ({
            ...state,
            storageFiles: [],
            getStorageFilesError: { statusCode: error.statusCode, message: error.message },
            getStorageFilesLoadingState: LoadingState.Error,
          }));
          return;
        }
        setState((prev) => ({
          ...prev,
          storageFiles: retVal ?? [],
          getProductsByUrlError: null,
          getStorageFilesLoadingState: LoadingState.Completed,
        }));
      } catch (err) {
        logger.error(err);
        setState((prev) => ({
          ...prev,
          storageFiles: [],
          getProductsByUrlError: { statusCode: 500, message: 'Something went wrong' },
          getStorageFilesLoadingState: LoadingState.Error,
        }));
      }
    };

    setState(() => ({
      ...state,
      storageFiles: [],
      getStorageFilesError: null,
      getStorageFilesLoadingState: LoadingState.Idle,
    }));

    fetchData();
  }, []);

  // Provide the fetched data via context
  return <StorageFilesContext.Provider value={state}>{children}</StorageFilesContext.Provider>;
};

export const StorageFilesConsumer = StorageFilesContext.Consumer;
