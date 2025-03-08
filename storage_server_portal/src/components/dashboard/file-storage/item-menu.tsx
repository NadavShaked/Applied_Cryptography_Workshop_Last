import * as React from 'react';
import ListItemIcon from '@mui/material/ListItemIcon';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import { FileArrowDown as FileArrowDownIcon } from '@phosphor-icons/react/dist/ssr/FileArrowDown';
import { Trash as TrashIcon } from '@phosphor-icons/react/dist/ssr/Trash';

export interface ItemMenuProps {
  anchorEl?: HTMLElement | null;
  onClose?: () => void;
  onDownload?: () => void;
  onDelete?: () => void;
  open?: boolean;
}

export function ItemMenu({ anchorEl, onClose, onDownload, onDelete, open = false }: ItemMenuProps): React.JSX.Element {
  return (
    <Menu
      anchorEl={anchorEl}
      anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      onClose={onClose}
      open={open}
      transformOrigin={{ horizontal: 'right', vertical: 'top' }}
    >
      <MenuItem onClick={onDownload}>
        <ListItemIcon>
          <FileArrowDownIcon />
        </ListItemIcon>
        Download
      </MenuItem>
      <MenuItem onClick={onDelete} sx={{ color: 'var(--mui-palette-error-main)' }}>
        <ListItemIcon>
          <TrashIcon />
        </ListItemIcon>
        Delete
      </MenuItem>
    </Menu>
  );
}
