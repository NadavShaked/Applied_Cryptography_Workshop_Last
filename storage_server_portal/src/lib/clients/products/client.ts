'use client';

import { StorageFile } from '@/types/storage-files/storage-file';
import { config } from '@/config';
import { GetStorageFilesResponseDto } from '@/lib/models/response/products-controller/get-products-response-dto';
import { ErrorStatus } from '@/contexts/storage-files/types';

import { getRequest, Result, ResultWithData } from '../../services/api-requests';

const errorMessageMap: Record<number, string> = {
  0: 'Something went wrong, please try again later',
  422: 'The URL must be a Fanatics product or multi-products URL.',
  500: 'Something went wrong, please try again later',
};

export interface GetProductDetailsParams {
  url: string;
}

export interface PublishProductsParams {
  products: StorageFile[];
  storeIds: number[];
}

class StorageFilesClient {
  async GetStorageFiles(): Promise<{ data?: any[] | null; error?: ErrorStatus }> {
    const getFilesEndoint: string = 'api/get_files';
    const response = await getRequest<ResultWithData<GetStorageFilesResponseDto>>(getFilesEndoint);

    if (response.statusCode >= 400 && response.statusCode < 600) {
      return {
        error: {
          statusCode: response.statusCode,
          message: errorMessageMap[response.statusCode] ?? errorMessageMap[0],
        },
      };
    }

    const storageFiles: StorageFile[] = response.result.data.storageFiles;

    return {
      data: storageFiles,
    };
  }

  async DeleteStorageFiles(fileName: string): Promise<{ data?: string | null; error?: ErrorStatus }> {
    const deleteFileEndoint: string = 'api/delete_file';
    const response = await getRequest<Result>(`${deleteFileEndoint}?filename=${fileName}`);

    if (response.statusCode >= 400 && response.statusCode < 600) {
      return {
        error: {
          statusCode: response.statusCode,
          message: errorMessageMap[response.statusCode] ?? errorMessageMap[0],
        },
      };
    }

    return {
      data: response.result.message,
    };
  }

  // async DownloadFiles(fileName: string): Promise<{ data?: string | null; error?: ErrorStatus }> {
  //   const downloadFileEndoint: string = 'api/download';
  //   const response = await getRequest<Result>(`${downloadFileEndoint}?filename=${fileName}`);

  //   if (response.statusCode >= 400 && response.statusCode < 600) {
  //     return {
  //       error: {
  //         statusCode: response.statusCode,
  //         message: errorMessageMap[response.statusCode] ?? errorMessageMap[0],
  //       },
  //     };
  //   }

  //   // Convert the response to a blob
  //   const blob = await response.blob();
  //   const url = window.URL.createObjectURL(blob);

  //   // Create a temporary <a> element to trigger the download
  //   const a = document.createElement('a');
  //   a.href = url;
  //   a.download = fileName;
  //   document.body.appendChild(a);
  //   a.click();

  //   // Cleanup
  //   window.URL.revokeObjectURL(url);
  //   document.body.removeChild(a);

  //   return {
  //     data: response.result.message,
  //   };
  // }

  // async PublishProducts(params: PublishProductsParams): Promise<{ data?: any[] | null; error?: ErrorStatus }> {
  //   const createProductsRequest: CreateProductsRequestDto = params;

  //   if (!createProductsRequest.products || createProductsRequest.products.length === 0) {
  //     return {};
  //   }

  //   if (!createProductsRequest.storeIds || createProductsRequest.storeIds.length === 0) {
  //     return {};
  //   }

  //   const response = await postRequest<ResultWithData<FanaticsProduct[]>>(
  //     createProductsEndpoint,
  //     '',
  //     {},
  //     createProductsRequest
  //   );

  //   if (response.statusCode >= 400 && response.statusCode < 600) {
  //     return {
  //       error: {
  //         statusCode: response.statusCode,
  //         message: errorMessageMap[response.statusCode] ?? errorMessageMap[DEFAULT_ERROR_KEY],
  //       },
  //     };
  //   }

  //   const products: FanaticsProduct[] = response.result.data;

  //   return {
  //     data: products,
  //   };
  // }

  async DownloadFiles(fileName: string): Promise<{ error?: ErrorStatus }> {
    const downloadFileEndpoint = `${config.apiService.apiServiceUrl}/api/download?filename=${fileName}`;

    try {
      const response = await fetch(downloadFileEndpoint, {
        method: 'GET',
        headers: {},
      });

      if (!response.ok) {
        return {
          error: {
            statusCode: response.status,
            message: errorMessageMap[response.status] ?? errorMessageMap[0],
          },
        };
      }

      // Convert response to a Blob
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);

      // Trigger file download
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName; // Set filename
      document.body.appendChild(a);
      a.click();

      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      return {}; // Success case (no error)
    } catch (error) {
      console.error('Download error:', error);
      return {
        error: {
          statusCode: 500,
          message: 'Failed to download file',
        },
      };
    }
  }
}

export const storageFilesClient = new StorageFilesClient();
