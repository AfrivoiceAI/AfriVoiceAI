const DEFAULT_DEV_API_BASE = 'http://localhost:8000/api/v1';
const configuredApiBase = import.meta.env.VITE_API_URL?.trim().replace(/\/+$/, '');
const API_BASE = configuredApiBase || (import.meta.env.DEV ? DEFAULT_DEV_API_BASE : '');

export function getToken(): string | null {
  return localStorage.getItem('av_token');
}

function getErrorDetail(payload: unknown): string | undefined {
  if (typeof payload !== 'object' || payload === null || !('detail' in payload)) {
    return undefined;
  }

  return typeof payload.detail === 'string' ? payload.detail : undefined;
}

export async function api<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  if (!API_BASE) {
    throw new Error('API is not configured for this deployment. Set VITE_API_URL and redeploy.');
  }

  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const token = getToken();
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const endpointPath = path.startsWith('/') ? path : `/${path}`;
  let response: Response;

  try {
    response = await fetch(`${API_BASE}${endpointPath}`, { ...options, headers });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(
        `Could not reach the API at ${API_BASE}. Check the API service and its CORS_ORIGINS setting.`,
      );
    }

    throw error;
  }

  const responseText = await response.text();
  let payload: unknown;

  if (responseText.trim()) {
    try {
      payload = JSON.parse(responseText);
    } catch {
      if (!response.ok) {
        throw new Error(`API request failed (${response.status}) with a non-JSON response.`);
      }

      throw new Error('The API returned an invalid JSON response.');
    }
  }

  if (!response.ok) {
    throw new Error(getErrorDetail(payload) || `API request failed (${response.status}).`);
  }

  if (payload === undefined) {
    throw new Error('The API returned an empty response.');
  }

  return payload as T;
}
