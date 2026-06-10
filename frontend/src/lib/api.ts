import axios from "axios";
import { API_URL } from "@/env";
import useAuthHeader from "react-auth-kit/hooks/useAuthHeader";
import { useMutation, useQuery } from "@tanstack/react-query";
import { z } from "zod";
import { QueryClient } from "@tanstack/react-query";

const api = axios.create({
  baseURL: API_URL,
});

const fetcher = (url: string, autheader: string) =>
  api
    .get(url, {
      headers: {
        Authorization: autheader,
      },
    })
    .then((res) => res.data);

export const useGet = <T>(
  url: string,
  schema: z.ZodType<T>,
  path_params?: string[],
  url_params?: { [key: string]: string }
) => {
  const authHeader = useAuthHeader();
  if (!authHeader) {
    throw new Error(
      "No auth header found but tried to fetch a protected endpoint"
    );
  }
  const base_url = url;
  // encode path params and append to url
  if (path_params) {
    for (const param of path_params) {
      url += `/${encodeURIComponent(param)}`;
    }
  }
  // encode url params and attach to url
  if (url_params) {
    url += "?";
    for (const [key, value] of Object.entries(url_params)) {
      url += `${key}=${encodeURIComponent(value)}&`;
    }
    url = url.slice(0, -1);
  }
  const queryKey = [
    base_url,
    ...(path_params || []),
    ...(url_params
      ? Object.entries(url_params).map(([key, value]) => `${key}=${value}`)
      : []),
  ];
  const { data, error, isLoading } = useQuery<T>({
    queryKey: queryKey,
    queryFn: () => fetcher(url, authHeader),
    retry: (failureCount, error) => {
      // if it's a 4xx error, don't retry
      if (axios.isAxiosError(error)) {
        const status = error.response?.status;
        if (status && status >= 400 && status < 500) {
          return false;
        }
      }
      // otherwise, retry
      return failureCount < 3;
    },
    staleTime: 1000 * 60 * 30, // 30 minutes
  });
  if (isLoading || error) {
    return {
      data: null,
      error: error,
      isLoading: isLoading,
    };
  }

  const parsedData = schema.parse(data);
  return {
    data: parsedData,
    error: null,
    isLoading: false,
  };
};

const pollFetcher = (url: string, autheader: string) =>
  api
    .get(url, {
      headers: {
        Authorization: autheader,
      },
    })
    .then((res) => {
      return {
        status: res.status,
        data: res.data,
      };
    });

export const usePoll = <T>(
  url: string,
  schema: z.ZodType<T>,
  path_params?: string[],
  url_params?: { [key: string]: string }
) => {
  const authHeader = useAuthHeader();
  if (!authHeader) {
    throw new Error(
      "No auth header found but tried to fetch a protected endpoint"
    );
  }
  // encode path params and append to url
  if (path_params) {
    for (const param of path_params) {
      url += `/${encodeURIComponent(param)}`;
    }
  }
  // encode url params and attach to url
  if (url_params) {
    url += "?";
    for (const [key, value] of Object.entries(url_params)) {
      url += `${key}=${encodeURIComponent(value)}&`;
    }
    url = url.slice(0, -1);
  }
  const { data, error, isLoading } = useQuery<{ data: T; status: number }>({
    queryKey: [
      url,
      ...(path_params || []),
      ...(url_params
        ? Object.entries(url_params).map(([key, value]) => `${key}=${value}`)
        : []),
    ],
    queryFn: () => pollFetcher(url, authHeader),
    retry: false,
    refetchInterval: (query) => {
      const status = query.state.data?.status;

      // Only continue polling if response status is 202 (Accepted)
      if (status === 202) {
        return 1000; // Poll every second
      }

      return Infinity;
    },
    refetchIntervalInBackground: true,
  });
  if (isLoading || error || !data?.data) {
    return {
      data: null,
      error: error,
      isLoading: isLoading,
    };
  }

  const parsedData = schema.parse(data.data);
  return {
    data: parsedData,
    error: null,
    isLoading: false,
  };
};

const postFetcher = <T, K>(url: string, data: T, authHeader: string) =>
  api
    .post(url, data, {
      headers: {
        Authorization: authHeader,
      },
    })
    .then((res) => res.data as K);

export const usePost = <T, K>(
  url: string,
  path_params?: string[],
  onSuccess?: (_: K) => void
) => {
  const authHeader = useAuthHeader();
  if (!authHeader) {
    throw new Error(
      "No auth header found but tried to fetch a protected endpoint"
    );
  }
  // encode path params and append to url
  if (path_params) {
    for (const param of path_params) {
      url += `/${encodeURIComponent(param)}`;
    }
  }
  const mutationFunc = <T, K>(data: T) =>
    postFetcher<T, K>(url, data, authHeader);
  return useMutation<K, Error, T>({
    mutationKey: [url, ...(path_params || [])],
    mutationFn: mutationFunc,
    onSuccess: onSuccess,
  });
};

const putFetcher = <T>(url: string, data: T, authHeader: string) =>
  api
    .put(url, data, {
      headers: {
        Authorization: authHeader,
      },
    })
    .then(() => null);

const deleteFetcher = <T>(url: string, data: T, authHeader: string) =>
  api
    .delete(url, {
      headers: {
        Authorization: authHeader,
      },
      data: data,
    })
    .then(() => null);

export const usePut = <T>(url: string, path_params?: string[]) => {
  const authHeader = useAuthHeader();
  if (!authHeader) {
    throw new Error(
      "No auth header found but tried to fetch a protected endpoint"
    );
  }
  // encode path params and append to url
  if (path_params) {
    for (const param of path_params) {
      url += `/${encodeURIComponent(param)}`;
    }
  }
  const mutationFunc = <T>(data: T) => putFetcher<T>(url, data, authHeader);
  return useMutation<null, Error, T>({
    mutationFn: mutationFunc,
    mutationKey: [url, ...(path_params || [])],
  });
};

export const useDelete = <T>(url: string, path_params?: string[]) => {
  const authHeader = useAuthHeader();
  if (!authHeader) {
    throw new Error(
      "No auth header found but tried to fetch a protected endpoint"
    );
  }
  // encode path params and append to url
  if (path_params) {
    for (const param of path_params) {
      url += `/${encodeURIComponent(param)}`;
    }
  }
  const mutationFunc = <T>(data: T) => deleteFetcher<T>(url, data, authHeader);
  return useMutation<null, Error, T>({
    mutationFn: mutationFunc,
    mutationKey: [url, ...(path_params || [])],
  });
};

export function populateQueryCache(
  queryClient: QueryClient,
  data: any,
  query_key: string[]
) {
  queryClient.setQueryData(query_key, data);
}
