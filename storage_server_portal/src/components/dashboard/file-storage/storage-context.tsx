'use client';

import * as React from 'react';
import { useContext } from 'react';

import { StorageFile } from '@/types/storage-files/storage-file';
import { StorageFilesContext } from '@/contexts/storage-files/storage-files-context';
import { StorageFilesContextValue } from '@/contexts/storage-files/types';

function noop(): void {
  return undefined;
}

export interface StorageContextValue {
  items: Map<string, StorageFile>;
  currentItemId?: string;
  setCurrentItemId: (itemId?: string) => void;
  downloadItem: (itemId: string) => void;
  deleteItem: (itemId: string) => void;
  favoriteItem: (itemId: string, value: boolean) => void;
}

export const StorageContext = React.createContext<StorageContextValue>({
  items: new Map(),
  setCurrentItemId: noop,
  downloadItem: noop,
  deleteItem: noop,
  favoriteItem: noop,
});

export interface StorageProviderProps {
  children: React.ReactNode;
  items: StorageFile[];
}

export function StorageProvider({ children, items: initialItems = [] }: StorageProviderProps): React.JSX.Element {
  const storageFilesStore = useContext<StorageFilesContextValue | undefined>(StorageFilesContext);

  const [items, setItems] = React.useState(new Map<string, StorageFile>());
  const [currentItemId, setCurrentItemId] = React.useState<string>();

  React.useEffect((): void => {
    setItems(new Map(initialItems.map((item) => [item.id, item])));
  }, [initialItems]);

  const handleDeleteItem = React.useCallback(
    (itemId: string) => {
      const item = items.get(itemId);

      // Item might no longer exist
      if (!item) {
        return;
      }

      if (item?.file_name) {
        storageFilesStore?.deleteStorageFile(item?.file_name);
      }

      const updatedItems = new Map<string, StorageFile>(items);

      // Delete item
      updatedItems.delete(itemId);

      // Dispatch update
      setItems(updatedItems);
    },
    [items]
  );

  const handleDownloadItem = React.useCallback(
    (itemId: string) => {
      const item = items.get(itemId);

      // Item might no longer exist
      if (!item) {
        return;
      }

      if (item?.file_name) {
        storageFilesStore?.downloadFile(item?.file_name);
      }
    },
    [items]
  );

  const handleFavoriteItem = React.useCallback(
    (itemId: string, value: boolean) => {
      const item = items.get(itemId);

      // Item might no longer exist
      if (!item) {
        return;
      }

      const updatedItems = new Map<string, StorageFile>(items);

      // Update item
      updatedItems.set(itemId, { ...item });

      // Dispatch update
      setItems(updatedItems);
    },
    [items]
  );

  return (
    <StorageContext.Provider
      value={{
        items,
        currentItemId,
        setCurrentItemId,
        downloadItem: handleDownloadItem,
        deleteItem: handleDeleteItem,
        favoriteItem: handleFavoriteItem,
      }}
    >
      {children}
    </StorageContext.Provider>
  );
}

export const StorageConsumer = StorageContext.Consumer;
