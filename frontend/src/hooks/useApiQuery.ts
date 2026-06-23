import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
  type QueryKey,
  type UseMutationOptions,
  type UseQueryOptions,
} from "@tanstack/react-query";
import { useCallback, useMemo } from "react";
import { useAuth } from "@/context/AuthContext";
import { ApiError, apiFetch } from "@/lib/apiClient";

type ApiQueryOptions<T> = Omit<
  UseQueryOptions<T, Error, T, QueryKey>,
  "queryKey" | "queryFn"
> & {
  keepPrevious?: boolean;
};

type ApiMutationOptions<TData, TVariables> = Omit<
  UseMutationOptions<TData, Error, TVariables>,
  "mutationFn"
> & {
  mutationFn: (
    variables: TVariables,
    request: <T>(path: string, init?: RequestInit) => Promise<T>,
  ) => Promise<TData>;
  invalidate?: readonly QueryKey[];
};

async function responseData<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let data: unknown;
    try {
      data = await response.json();
    } catch {
      data = undefined;
    }
    const detail =
      data && typeof data === "object" && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : `Request failed (${response.status})`;
    throw new ApiError(detail, response.status, data);
  }

  if (response.status === 204) return undefined as T;
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) return undefined as T;
  return response.json() as Promise<T>;
}

export function useApiRequest() {
  const { tokens, setTokens, logout } = useAuth();

  return useCallback(
    async <T,>(path: string, init: RequestInit = {}): Promise<T> => {
      const response = await apiFetch(path, init, tokens, setTokens, logout);
      return responseData<T>(response);
    },
    [logout, setTokens, tokens],
  );
}

export function useSessionQueryKey(parts: QueryKey): QueryKey {
  const { user } = useAuth();
  const scope = user ? `${user.role}:${user.id}` : "anonymous";
  return useMemo(() => ["session", scope, ...parts], [scope, parts]);
}

export function useApiQuery<T>(
  parts: QueryKey,
  path: string,
  options: ApiQueryOptions<T> = {},
) {
  const request = useApiRequest();
  const queryKey = useSessionQueryKey(parts);
  const { keepPrevious, ...queryOptions } = options;

  return useQuery<T, Error>({
    queryKey,
    queryFn: ({ signal }) => request<T>(path, { method: "GET", signal }),
    placeholderData: keepPrevious ? keepPreviousData : undefined,
    ...queryOptions,
  });
}

export function useApiMutation<TData = unknown, TVariables = void>(
  options: ApiMutationOptions<TData, TVariables>,
) {
  const request = useApiRequest();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const { mutationFn, invalidate = [], onSuccess, ...mutationOptions } = options;
  const scope = user ? `${user.role}:${user.id}` : "anonymous";
  const scopedKeys = invalidate.map((key) => ["session", scope, ...key]);

  return useMutation<TData, Error, TVariables>({
    ...mutationOptions,
    mutationFn: (variables) => mutationFn(variables, request),
    onSuccess: async (data, variables, context) => {
      await Promise.all(
        scopedKeys.map((queryKey) => queryClient.invalidateQueries({ queryKey })),
      );
      await onSuccess?.(data, variables, context);
    },
  });
}

export function useSessionCache() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const scope = user ? `${user.role}:${user.id}` : "anonymous";

  const key = useCallback(
    (parts: QueryKey): QueryKey => ["session", scope, ...parts],
    [scope],
  );

  const invalidate = useCallback(
    (...parts: QueryKey[]) =>
      Promise.all(
        parts.map((queryKey) =>
          queryClient.invalidateQueries({ queryKey: key(queryKey) }),
        ),
      ),
    [key, queryClient],
  );

  return { queryClient, key, invalidate };
}
