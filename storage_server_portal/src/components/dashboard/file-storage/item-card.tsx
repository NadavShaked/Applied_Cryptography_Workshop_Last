'use client';

import * as React from 'react';
import Avatar from '@mui/material/Avatar';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import { DotsThree as DotsThreeIcon } from '@phosphor-icons/react/dist/ssr/DotsThree';
import { Globe as GlobeIcon } from '@phosphor-icons/react/dist/ssr/Globe';
import { Star as StarIcon } from '@phosphor-icons/react/dist/ssr/Star';

import { StorageFile } from '@/types/storage-files/storage-file';
import { usePopover } from '@/hooks/use-popover';

import { ItemIcon } from './item-icon';
import { ItemMenu } from './item-menu';

export interface ItemCardProps {
  item: StorageFile;
  onDelete?: (itemId: string) => void;
  onFavorite?: (itemId: string, value: boolean) => void;
  onOpen?: (itemId: string) => void;
}

export function ItemCard({ item, onDelete, onFavorite, onOpen }: ItemCardProps): React.JSX.Element {
  const popover = usePopover<HTMLButtonElement>();

  const handleDelete = React.useCallback(() => {
    popover.handleClose();
    onDelete?.(item.id);
  }, [item, popover, onDelete]);

  const isFavorite = true;

  return (
    <React.Fragment>
      <Card
        key={item.id}
        sx={{
          transition: 'box-shadow 200ms cubic-bezier(0.4, 0, 0.2, 1) 0ms',
          '&:hover': { boxShadow: 'var(--mui-shadows-16)' },
        }}
      >
        <Stack direction="row" spacing={3} sx={{ alignItems: 'center', justifyContent: 'space-between', pt: 2, px: 2 }}>
          <IconButton
            onClick={() => {
              onFavorite?.(item.id, !isFavorite);
            }}
          >
            <StarIcon color="var(--mui-palette-warning-main)" weight={isFavorite ? 'fill' : undefined} />
          </IconButton>
          <IconButton onClick={popover.handleOpen} ref={popover.anchorRef}>
            <DotsThreeIcon weight="bold" />
          </IconButton>
        </Stack>
        <Stack divider={<Divider />} spacing={1} sx={{ p: 2 }}>
          <Box
            onClick={() => {
              onOpen?.(item.id);
            }}
            sx={{ display: 'inline-flex', cursor: 'pointer' }}
          >
            <ItemIcon extension={'item.extension'} type={'file'} />
          </Box>
          <div>
            <Typography
              onClick={() => {
                onOpen?.(item.id);
              }}
              sx={{ cursor: 'pointer' }}
              variant="subtitle2"
            >
              {item.file_name}
            </Typography>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                {true ? (
                  <Tooltip title="Public">
                    <Avatar sx={{ '--Avatar-size': '32px' }}>
                      <GlobeIcon fontSize="var(--Icon-fontSize)" />
                    </Avatar>
                  </Tooltip>
                ) : null}
              </div>
            </Stack>
            <Stack>
              <Typography color="text.secondary" variant="caption">
                Created at {item.last_verify}
              </Typography>
            </Stack>
            <Stack>
              <Typography color="text.secondary" variant="caption">
                Escrow Public Key: {item.escrow_public_key}
              </Typography>
            </Stack>
          </div>
        </Stack>
      </Card>
      <ItemMenu
        anchorEl={popover.anchorRef.current}
        onClose={popover.handleClose}
        onDelete={handleDelete}
        open={popover.open}
      />
    </React.Fragment>
  );
}
