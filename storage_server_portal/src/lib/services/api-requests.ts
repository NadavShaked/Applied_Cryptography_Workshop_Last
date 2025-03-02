import { config } from '@/config';

export interface Pagination {
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
}

export interface Result {
  message: string;
}

export interface ResultWithData<Tdata = any> extends Result {
  data: Tdata;
  pagination?: Pagination;
}

export interface ResultWithMeta<Tdata = any, Tmeta = any> extends ResultWithData<Tdata> {
  meta: Tmeta;
}

export interface ResponseWithResult<T extends Result> {
  statusCode: number;
  result: T;
}

export interface IRequestHeader {
  [key: string]: string;
}

enum HttpMethod {
  GET = 'GET',
  POST = 'POST',
  PUT = 'PUT',
  DELETE = 'DELETE',
  PATCH = 'PATCH',
}

export const getRequest = async <T extends ResultWithMeta | ResultWithData | Result>(
  endpoint: string,
  qParams: string = '',
  additionalHeaders: IRequestHeader = {}
): Promise<ResponseWithResult<T>> => request(HttpMethod.GET, endpoint, qParams, additionalHeaders);

export const postRequest = async <T extends ResultWithMeta | ResultWithData | Result>(
  endpoint: string,
  qParams: string = '',
  additionalHeaders: IRequestHeader = {},
  body: any
): Promise<ResponseWithResult<T>> => request(HttpMethod.POST, endpoint, qParams, additionalHeaders, body);

export const putRequest = async <T extends ResultWithMeta | ResultWithData | Result>(
  endpoint: string,
  qParams: string = '',
  additionalHeaders: IRequestHeader = {},
  body: any
): Promise<ResponseWithResult<T>> => request(HttpMethod.PUT, endpoint, qParams, additionalHeaders, body);

export const deleteRequest = async <T extends ResultWithMeta | ResultWithData | Result>(
  endpoint: string,
  qParams: string = '',
  additionalHeaders: IRequestHeader = {},
  body: any
): Promise<ResponseWithResult<T>> => request(HttpMethod.DELETE, endpoint, qParams, additionalHeaders, body);

export const patchRequest = async <T extends ResultWithMeta | ResultWithData | Result>(
  endpoint: string,
  qParams: string = '',
  additionalHeaders: IRequestHeader = {},
  body: any
): Promise<ResponseWithResult<T>> => request(HttpMethod.PATCH, endpoint, qParams, additionalHeaders, body);

const request = async <T extends ResultWithMeta | ResultWithData | Result>(
  httpMethod: HttpMethod,
  endpoint: string,
  qParams: string = '',
  headers: IRequestHeader = {},
  body: any = undefined
): Promise<ResponseWithResult<T>> => {
  headers['Content-Type'] = 'application/json';

  const queryParam = qParams ? `?${qParams}` : '';

  const response = await fetch(`${config.apiService.apiServiceUrl}/${endpoint}${queryParam}`, {
    method: httpMethod,
    headers: headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  const statusCode = response.status;
  const result = await response.json();

  // Check and return appropriate Result types
  if (result.meta) {
    return {
      statusCode: statusCode,
      result: {
        message: result.message,
        data: result.data,
        pagination: result.pagination,
        meta: result.meta,
      } as T,
    };
  } else if (result.data) {
    return {
      statusCode: statusCode,
      result: {
        message: result.message,
        data: result.data,
        pagination: result.pagination,
      } as T,
    };
  } else {
    return {
      statusCode: statusCode,
      result: {
        message: result.message || 'No data found',
      } as T,
    };
  }
};
