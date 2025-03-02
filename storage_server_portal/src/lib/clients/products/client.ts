'use client';

import { StorageFile } from '@/types/storage-files/storage-file';
import { GetStorageFilesResponseDto } from '@/lib/models/response/products-controller/get-products-response-dto';
import { ErrorStatus } from '@/contexts/storage-files/types';

import { getRequest, postRequest, Result, ResultWithData } from '../../services/api-requests';

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
    const deleteFilesEndoint: string = 'api/delete_files';
    const response = await getRequest<Result>(`${deleteFilesEndoint}?filename=${fileName}`);

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
}

export const storageFilesClient = new StorageFilesClient();
