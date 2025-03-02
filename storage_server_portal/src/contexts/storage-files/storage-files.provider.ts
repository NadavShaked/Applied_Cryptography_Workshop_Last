import type * as React from 'react';

import {
  StorageFilesContext as CustomStorageFilesContext,
  StorageFilesProvider as CustomStorageFilesProvider,
  StorageFilesProviderProps,
} from './storage-files-context';
import type { StorageFilesContextValue } from './types';

// eslint-disable-next-line import/no-mutable-exports -- Export based on config
let StorageFilesProvider: React.FC<StorageFilesProviderProps>;

// eslint-disable-next-line import/no-mutable-exports -- Export based on config
let StorageFilesContext: React.Context<StorageFilesContextValue | undefined>;

StorageFilesContext = CustomStorageFilesContext;
StorageFilesProvider = CustomStorageFilesProvider;

export { StorageFilesProvider as StorageFilesProvider, StorageFilesContext as StorageFilesContext };
