'use client';

import * as React from 'react';
import Avatar from '@mui/material/Avatar';
import AvatarGroup from '@mui/material/AvatarGroup';
import Box from '@mui/material/Box';
import Dialog from '@mui/material/Dialog';
import DialogContent from '@mui/material/DialogContent';
import IconButton from '@mui/material/IconButton';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Unstable_Grid2';
import { Globe as GlobeIcon } from '@phosphor-icons/react/dist/ssr/Globe';
import { PencilSimple as PencilSimpleIcon } from '@phosphor-icons/react/dist/ssr/PencilSimple';
import { Plus as PlusIcon } from '@phosphor-icons/react/dist/ssr/Plus';
import { Star as StarIcon } from '@phosphor-icons/react/dist/ssr/Star';
import { X as XIcon } from '@phosphor-icons/react/dist/ssr/X';

import { StorageFile } from '@/types/storage-files/storage-file';
import { dayjs } from '@/lib/dayjs';
import { usePopover } from '@/hooks/use-popover';

import { ItemIcon } from './item-icon';

const tagOptions = ['Personal', 'Work', 'Business', 'Accounting', 'Security', 'Design'] satisfies string[];

export interface ItemModalProps {
  item: StorageFile;
  onClose?: () => void;
  onDownload?: (itemId: string) => void;
  onDelete?: (itemId: string) => void;
  onFavorite?: (itemId: string, value: boolean) => void;
  open?: boolean;
}

export function ItemModal({ item, onClose, onDownload, onDelete, onFavorite, open = false }: ItemModalProps): React.JSX.Element {
  const tagsPopover = usePopover<HTMLButtonElement>();

  const sharedWith = ['shared'];
  const showShared = true;

  const isFavorite = true;

  return (
    <React.Fragment>
      <Dialog
        maxWidth="sm"
        onClose={onClose}
        open={open}
        sx={{
          '& .MuiDialog-container': { justifyContent: 'flex-end' },
          '& .MuiDialog-paper': { height: '100%', width: '100%' },
        }}
      >
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', minHeight: 0, p: 0 }}>
          <Stack
            direction="row"
            spacing={2}
            sx={{
              alignItems: 'center',
              borderBottom: '1px solid var(--mui-palette-divider)',
              flex: '0 0 auto',
              justifyContent: 'space-between',
              p: 3,
            }}
          >
            <IconButton
              onClick={() => {
                onFavorite?.(item.id, !isFavorite);
              }}
            >
              <StarIcon color="var(--mui-palette-warning-main)" weight={isFavorite ? 'fill' : undefined} />
            </IconButton>
            <IconButton onClick={onClose}>
              <XIcon />
            </IconButton>
          </Stack>
          <Stack spacing={2} sx={{ flex: '1 1 auto', minHeight: 0, overflowY: 'auto', px: 3, py: 2 }}>
            <Box
              sx={{
                border: '1px dashed var(--mui-palette-divider)',
                borderRadius: 1,
                display: 'flex',
                flex: '0 0 auto',
                justifyContent: 'center',
                p: 3,
              }}
            >
              <ItemIcon extension={'item.extension'} type={'file'} />
            </Box>
            <Stack direction="row" spacing={2} sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="h6">{item.file_name}</Typography>
              <IconButton>
                <PencilSimpleIcon />
              </IconButton>
            </Stack>
            <div>
              <Grid alignItems="center" container spacing={3}>
                <Grid sm={4} xs={12}>
                  <Typography color="text.secondary" variant="body2">
                    Created by
                  </Typography>
                </Grid>
                <Grid sm={8} xs={12}>
                  {/* {item.author ? <Avatar src={item.author.avatar} /> : null} */}
                  {true ? <Avatar src={'item.author.avatar'} /> : null}
                </Grid>
                <Grid sm={8} xs={12}>
                  <Typography variant="body2">
                    {item.last_verify ? dayjs(item.last_verify).format('MMM D, YYYY hh:mm A') : undefined}
                  </Typography>
                </Grid>
                <Grid sm={4} xs={12}>
                  <Typography color="text.secondary" variant="body2">
                    Modified At
                  </Typography>
                </Grid>
                <Grid sm={8} xs={12}>
                  <Typography variant="body2">
                    {item.last_verify ? dayjs(item.last_verify).format('MMM D, YYYY hh:mm A') : undefined}
                  </Typography>
                </Grid>
                <Grid sm={4} xs={12}>
                  <Typography color="text.secondary" variant="body2">
                    Shared with
                  </Typography>
                </Grid>
                <Grid sm={8} xs={12}>
                  <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                    {true ? (
                      <Tooltip title="Public">
                        <Avatar sx={{ '--Avatar-size': '32px' }}>
                          <GlobeIcon fontSize="var(--Icon-fontSize)" />
                        </Avatar>
                      </Tooltip>
                    ) : null}
                    {showShared ? (
                      <AvatarGroup max={3}>
                        {sharedWith.map((person) => (
                          <Avatar key={'person.name'} src={'person.avatar'} sx={{ '--Avatar-size': '32px' }} />
                        ))}
                      </AvatarGroup>
                    ) : null}
                    <IconButton>
                      <PlusIcon />
                    </IconButton>
                  </Stack>
                </Grid>
              </Grid>
            </div>
          </Stack>
        </DialogContent>
      </Dialog>
      <Menu
        anchorEl={tagsPopover.anchorRef.current}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        onClose={tagsPopover.handleClose}
        open={tagsPopover.open}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
      >
        {tagOptions.map((option) => (
          <MenuItem key={option}>{option}</MenuItem>
        ))}
      </Menu>
    </React.Fragment>
  );
}
