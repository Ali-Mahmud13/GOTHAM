const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

type Tokens = { accessToken: string; refreshToken: string };

export class ApiError extends Error {
  constructor(message: string, public status?: number, public data?: unknown) {
    super(message);
    this.name = 'ApiError';
  }
}

async function parseError(res: Response): Promise<{ message: string; data?: unknown }> {
  let data: unknown;
  try {
    data = await res.json();
  } catch {
    // ignore
  }
  const detail =
    data && typeof data === 'object' && data !== null && 'detail' in data
      ? // eslint-disable-next-line @typescript-eslint/no-explicit-any
        String((data as any).detail)
      : undefined;
  return { message: detail || `API Error: ${res.status} ${res.statusText}`, data };
}

export async function refresh(tokens: Tokens): Promise<Tokens> {
  const res = await fetch(`${API_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: tokens.refreshToken }),
  });
  if (!res.ok) {
    const err = await parseError(res);
    throw new ApiError(err.message, res.status, err.data);
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const data: any = await res.json();
  if (!data?.access_token || !data?.refresh_token) {
    throw new ApiError('Refresh response missing tokens');
  }
  return { accessToken: data.access_token, refreshToken: data.refresh_token };
}

export async function apiFetch(
  input: string,
  init: RequestInit,
  tokens: Tokens | null,
  onTokens?: (t: Tokens) => void,
  onUnauthorized?: () => void,
): Promise<Response> {
  const doFetch = async (t: Tokens | null) => {
    const headers = new Headers(init.headers || {});
    if (t?.accessToken) headers.set('Authorization', `Bearer ${t.accessToken}`);
    return fetch(`${API_URL}${input}`, { ...init, headers });
  };

  let res = await doFetch(tokens);
  if (res.status !== 401 || !tokens) return res;

  try {
    const newTokens = await refresh(tokens);
    onTokens?.(newTokens);
    res = await doFetch(newTokens);
    if (res.status === 401) onUnauthorized?.();
    return res;
  } catch {
    onUnauthorized?.();
    return res;
  }
}

