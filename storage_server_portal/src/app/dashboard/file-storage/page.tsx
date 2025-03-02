import * as React from 'react';
import type { Metadata } from 'next';

import { config } from '@/config';
import { StorageFilesProvider } from '@/contexts/storage-files/storage-files-context';

import { StoragePage } from './storage-page';

export const metadata = { title: `File storage | Dashboard | ${config.site.name}` } satisfies Metadata;

interface PageProps {
  searchParams: { query?: string; sortDir?: 'asc' | 'desc'; view?: 'grid' | 'list' };
}

export default function Page({ searchParams }: PageProps): React.JSX.Element {
  return (
    <StorageFilesProvider>
      <StoragePage searchParams={searchParams} />
    </StorageFilesProvider>
  );
}
