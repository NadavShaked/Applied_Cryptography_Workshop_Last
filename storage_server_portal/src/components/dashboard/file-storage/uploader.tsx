import * as React from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogContent from '@mui/material/DialogContent';
import IconButton from '@mui/material/IconButton';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import { X as XIcon } from '@phosphor-icons/react/dist/ssr/X';

import type { File } from '@/components/core/file-dropzone';
import { FileDropzone } from '@/components/core/file-dropzone';
import { FileIcon } from '@/components/core/file-icon';

function bytesToSize(bytes: number, decimals = 2): string {
  if (bytes === 0) {
    return '0 Bytes';
  }

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

export interface UploaderProps {
  onClose?: () => void;
  open?: boolean;
}

export function Uploader({ onClose, open = false }: UploaderProps): React.JSX.Element {
  const [files, setFiles] = React.useState<File[]>([]);
  const [escrowPublicKey, setEscrowPublicKey] = React.useState<string>('');

  React.useEffect(() => {
    setFiles([]);
  }, [open]);

  const handleDrop = React.useCallback(
    (newFiles: File[]) => {
      // Ensure only one file can be selected
      if (newFiles.length > 0 && files.length === 0) {
        setFiles([newFiles[0]]); // Only accept the first file
      }
    },
    [files]
  );

  const handleRemove = React.useCallback((file: File) => {
    setFiles([]);
  }, []);

  const handleRemoveAll = React.useCallback(() => {
    setFiles([]);
  }, []);

  const handleUpload = async () => {
    if (!escrowPublicKey) {
      alert('Escrow public key is required');
      return;
    }

    const formData = new FormData();

    // Append the selected file to the form data
    if (files.length > 0) {
      formData.append('file', files[0]); // 'file' is the key expected on the server
    }

    // Append the escrow public key
    formData.append('escrow_public_key', escrowPublicKey);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        // Handle success (e.g., show a success message, reset state, etc.)
        const responseData = await response.json();
        alert('File uploaded successfully: ' + responseData.filename);
        setFiles([]); // Clear files after successful upload
        setEscrowPublicKey(''); // Clear escrow public key
      } else {
        // Handle error (e.g., show an error message)
        const errorData = await response.json();
        alert('Failed to upload file: ' + errorData.error);
      }
    } catch (error) {
      // Handle any errors that occur during the request
      console.error('Error uploading file:', error);
      alert('Error uploading file.');
    }
  };

  return (
    <Dialog fullWidth maxWidth="sm" onClose={onClose} open={open}>
      <Stack direction="row" spacing={3} sx={{ alignItems: 'center', justifyContent: 'space-between', px: 3, py: 2 }}>
        <Typography variant="h6">Upload file</Typography>
        <IconButton onClick={onClose}>
          <XIcon />
        </IconButton>
      </Stack>
      <DialogContent>
        <Stack spacing={3}>
          <Typography variant="subtitle2">Enter Escrow Public Key</Typography>
          <input
            type="text"
            value={escrowPublicKey}
            onChange={(e) => setEscrowPublicKey(e.target.value)}
            placeholder="Escrow Public Key"
            style={{ padding: '8px', width: '100%' }}
          />
          <FileDropzone
            accept={{ '*/*': [] }}
            caption="Max file size is 3 MB"
            files={files}
            onDrop={handleDrop}
            disabled={files.length >= 1} // Disable Dropzone when one file is selected
          />
          {files.length ? (
            <Stack spacing={2}>
              <Stack component="ul" spacing={1} sx={{ listStyle: 'none', m: 0, p: 0 }}>
                {files.map((file) => {
                  const extension = file.name.split('.').pop();

                  return (
                    <Stack
                      component="li"
                      direction="row"
                      key={file.path}
                      spacing={2}
                      sx={{
                        alignItems: 'center',
                        border: '1px solid var(--mui-palette-divider)',
                        borderRadius: 1,
                        flex: '1 1 auto',
                        p: 1,
                      }}
                    >
                      <FileIcon extension={extension} />
                      <Box sx={{ flex: '1 1 auto' }}>
                        <Typography variant="subtitle2">{file.name}</Typography>
                        <Typography color="text.secondary" variant="body2">
                          {bytesToSize(file.size)}
                        </Typography>
                      </Box>
                      <Tooltip title="Remove">
                        <IconButton
                          onClick={() => {
                            handleRemove(file);
                          }}
                        >
                          <XIcon />
                        </IconButton>
                      </Tooltip>
                    </Stack>
                  );
                })}
              </Stack>
              <Stack direction="row" spacing={2} sx={{ alignItems: 'center', justifyContent: 'flex-end' }}>
                <Button color="secondary" onClick={handleRemoveAll} size="small" type="button">
                  Remove all
                </Button>
                <Button onClick={handleUpload} size="small" type="button" variant="contained">
                  Upload
                </Button>
              </Stack>
            </Stack>
          ) : null}
        </Stack>
      </DialogContent>
    </Dialog>
  );
}
