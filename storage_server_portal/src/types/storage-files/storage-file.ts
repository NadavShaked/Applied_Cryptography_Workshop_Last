export interface StorageFile {
  id: string;
  file_name: string;
  escrow_public_key: string;
  validate_every: number;
  last_verify: string;
}
