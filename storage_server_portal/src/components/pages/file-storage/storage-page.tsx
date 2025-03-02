'use client';

import * as React from 'react';
import { useContext, useMemo } from 'react';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Unstable_Grid2';

import { StorageFile } from '@/types/storage-files/storage-file';
import { dayjs } from '@/lib/dayjs';
import { StorageFilesContext } from '@/contexts/storage-files/storage-files-context';
import { StorageFilesContextValue } from '@/contexts/storage-files/types';
import { ItemsFilters } from '@/components/dashboard/file-storage/items-filters';
import type { Filters } from '@/components/dashboard/file-storage/items-filters';
import { ItemsPagination } from '@/components/dashboard/file-storage/items-pagination';
import { StorageProvider } from '@/components/dashboard/file-storage/storage-context';
import { StorageView } from '@/components/dashboard/file-storage/storage-view';
import type { Item } from '@/components/dashboard/file-storage/types';
import { UplaodButton } from '@/components/dashboard/file-storage/upload-button';

const items = [
  {
    id: 'FILE-009',
    type: 'folder',
    name: 'AWS Credentials',
    author: { name: 'Sofia Rivers', avatar: '/assets/avatar.png' },
    isFavorite: true,
    isPublic: false,
    tags: ['Secrets', 'Important'],
    shared: [
      { name: 'Miron Vitold', avatar: '/assets/avatar-1.png' },
      { name: 'Alcides Antonio', avatar: '/assets/avatar-10.png' },
      { name: 'Nasimiyu Danai', avatar: '/assets/avatar-7.png' },
    ],
    itemsCount: 3,
    size: '5 MB',
    createdAt: dayjs().subtract(3, 'minute').subtract(4, 'hour').toDate(),
    updatedAt: dayjs().subtract(3, 'minute').subtract(4, 'hour').toDate(),
  },
  {
    id: 'FILE-008',
    type: 'folder',
    name: 'invoices',
    author: { name: 'Sofia Rivers', avatar: '/assets/avatar.png' },
    isFavorite: false,
    isPublic: false,
    tags: ['Work', 'Accounting'],
    shared: [],
    itemsCount: 71,
    size: '1.2 GB',
    createdAt: dayjs().subtract(16, 'minute').subtract(20, 'hour').toDate(),
    updatedAt: dayjs().subtract(16, 'minute').subtract(20, 'hour').toDate(),
  },
  {
    id: 'FILE-007',
    type: 'folder',
    name: 'assets',
    author: { name: 'Carson Darrin', avatar: '/assets/avatar-3.png' },
    isFavorite: false,
    isPublic: true,
    tags: [],
    shared: [],
    itemsCount: 12,
    size: '325.2 MB',
    createdAt: dayjs().subtract(23, 'minute').subtract(26, 'hour').toDate(),
    updatedAt: dayjs().subtract(23, 'minute').subtract(26, 'hour').toDate(),
  },
  {
    id: 'FILE-006',
    type: 'file',
    name: 'company-logo.svg',
    extension: 'svg',
    author: { name: 'Siegbert Gottfried', avatar: '/assets/avatar-2.png' },
    isFavorite: false,
    isPublic: false,
    tags: ['Work'],
    shared: [
      { name: 'Sofia Rivers', avatar: '/assets/avatar.png' },
      { name: 'Nasimiyu Danai', avatar: '/assets/avatar-7.png' },
    ],
    size: '1.2 MB',
    createdAt: dayjs().subtract(41, 'minute').subtract(6, 'hour').subtract(2, 'day').toDate(),
    updatedAt: dayjs().subtract(41, 'minute').subtract(6, 'hour').subtract(2, 'day').toDate(),
  },
  {
    id: 'FILE-005',
    type: 'file',
    name: 'devias-kit.fig',
    extension: 'pkg',
    author: { name: 'Sofia Rivers', avatar: '/assets/avatar.png' },
    isFavorite: true,
    isPublic: false,
    tags: ['Personal'],
    shared: [{ name: 'Omar Darobe', avatar: '/assets/avatar-11.png' }],
    size: '16.7 MB',
    createdAt: dayjs().subtract(11, 'minute').subtract(16, 'hour').subtract(18, 'day').toDate(),
    updatedAt: dayjs().subtract(11, 'minute').subtract(16, 'hour').subtract(18, 'day').toDate(),
  },
  {
    id: 'FILE-004',
    type: 'file',
    name: 'not_a_virus.exe',
    extension: 'exe',
    author: { name: 'Sofia Rivers', avatar: '/assets/avatar.png' },
    isFavorite: false,
    isPublic: false,
    tags: ['Security'],
    shared: [{ name: 'Siegbert Gottfried', avatar: '/assets/avatar-2.png' }],
    size: '13.37 KB',
    createdAt: dayjs().subtract(1, 'minute').subtract(3, 'hour').subtract(37, 'day').toDate(),
    updatedAt: dayjs().subtract(1, 'minute').subtract(3, 'hour').subtract(37, 'day').toDate(),
  },
  {
    id: 'FILE-003',
    type: 'file',
    name: 'website-hero-illustration.psd',
    extension: 'psd',
    author: { name: 'Sofia Rivers', avatar: '/assets/avatar.png' },
    isFavorite: false,
    isPublic: false,
    tags: ['Work', 'Design'],
    shared: [{ name: 'Siegbert Gottfried', avatar: '/assets/avatar-2.png' }],
    size: '2.3 MB',
    createdAt: dayjs().subtract(12, 'minute').subtract(11, 'hour').subtract(40, 'day').toDate(),
    updatedAt: dayjs().subtract(12, 'minute').subtract(11, 'hour').subtract(40, 'day').toDate(),
  },
  {
    id: 'FILE-002',
    type: 'file',
    name: 'ssl-certs.tar',
    extension: 'tar',
    author: { name: 'Sofia Rivers', avatar: '/assets/avatar.png' },
    isFavorite: false,
    isPublic: false,
    tags: ['Work', 'Security'],
    shared: [{ name: 'Omar Darobe', avatar: '/assets/avatar-11.png' }],
    size: '684.1 KB',
    createdAt: dayjs().subtract(15, 'minute').subtract(23, 'hour').subtract(41, 'day').toDate(),
    updatedAt: dayjs().subtract(15, 'minute').subtract(23, 'hour').subtract(41, 'day').toDate(),
  },
  {
    id: 'FILE-001',
    type: 'file',
    name: 'tablet-driver-adapter.deb',
    extension: 'deb',
    author: { name: 'Sofia Rivers', avatar: '/assets/avatar.png' },
    isFavorite: false,
    isPublic: false,
    tags: [],
    shared: [],
    size: '5.2 MB',
    createdAt: dayjs().subtract(40, 'minute').subtract(11, 'hour').subtract(62, 'day').toDate(),
    updatedAt: dayjs().subtract(40, 'minute').subtract(11, 'hour').subtract(62, 'day').toDate(),
  },
] satisfies Item[];

interface PageProps {
  searchParams: { query?: string; sortDir?: 'asc' | 'desc'; view?: 'grid' | 'list' };
}

export const StoragePage: React.FC<PageProps> = ({ searchParams }) => {
  const storageFilesStore = useContext<StorageFilesContextValue | undefined>(StorageFilesContext);

  const storageFiles: StorageFile[] = useMemo(
    () => storageFilesStore?.storageFiles ?? [],
    [storageFilesStore?.storageFiles]
  );

  const { query, sortDir, view = 'grid' } = searchParams;

  const filters = { query };

  const sortedItems: StorageFile[] = applySort(storageFiles, sortDir);
  const filteredItems: StorageFile[] = applyFilters(sortedItems, filters);

  return (
    <Box
      sx={{
        maxWidth: 'var(--Content-maxWidth)',
        m: 'var(--Content-margin)',
        p: 'var(--Content-padding)',
        width: 'var(--Content-width)',
      }}
    >
      <Stack spacing={4}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={3} sx={{ alignItems: 'flex-start' }}>
          <Box sx={{ flex: '1 1 auto' }}>
            <Typography variant="h4">File storage</Typography>
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <UplaodButton />
          </Box>
        </Stack>
        <Grid container spacing={4}>
          <Grid md={12} xs={12}>
            <Stack spacing={4}>
              <ItemsFilters filters={filters} sortDir={sortDir} view={view} />
              <StorageProvider items={filteredItems}>
                <StorageView view={view} />
              </StorageProvider>
              <ItemsPagination count={filteredItems.length} page={0} />
            </Stack>
          </Grid>
        </Grid>
      </Stack>
    </Box>
  );
};

// Sorting and filtering has to be done on the server.

function applySort(row: StorageFile[], sortDir: 'asc' | 'desc' | undefined): StorageFile[] {
  return row;
  // return row.sort((a, b) => {
  //   if (sortDir === 'asc') {
  //     return a.createdAt.getTime() - b.createdAt.getTime();
  //   }

  //   return b.createdAt.getTime() - a.createdAt.getTime();
  // });
}

function applyFilters(row: StorageFile[], { query }: Filters): StorageFile[] {
  return row.filter((item) => {
    if (query) {
      if (!item.file_name?.toLowerCase().includes(query.toLowerCase())) {
        return false;
      }
    }

    return true;
  });
}
