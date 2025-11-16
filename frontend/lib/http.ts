import { API_BASE } from "./config";

/**
 * 輔助函式：判斷是否為絕對 URL
 */
function isAbsoluteUrl(url: string): boolean {
  return url.startsWith('http://') || url.startsWith('https://');
}

/**
 * 輔助函式：建立完整 URL
 */
function buildUrl(path: string): string {
  return isAbsoluteUrl(path) ? path : `${API_BASE}${path}`;
}

/**
 * 輔助函式：自動建立並附加 'Authorization' 標頭 (如果 token 存在)
 */
function getAuthHeaders(): HeadersInit {
  // 僅在「瀏覽器環境」中執行 (Next.js 有時會在伺服器端執行)
  if (typeof window === 'undefined') {
    return {};
  }

  const token = localStorage.getItem('authToken');
  if (token) {
    return {
      'Authorization': `Bearer ${token}`
    };
  }
  return {};
}

/**
 * 是否在開發/本機環境下（用於額外把錯誤內容印到 console）
 */
function shouldLogHttpErrors(): boolean {
  if (typeof window === 'undefined') return false;
  const host = window.location.hostname || '';
  const isLocalHost = host === 'localhost' || host === '127.0.0.1' || host.endsWith('.local');
  const nodeEnv = (typeof process !== 'undefined' && (process as any).env && (process as any).env.NODE_ENV) || undefined;
  return isLocalHost || nodeEnv !== 'production';
}

async function handleNonOk(res: Response, path: string): Promise<never> {
  const text = await res.text().catch(() => '');
  if (shouldLogHttpErrors()) {
    try {
      const maybeJson = JSON.parse(text);
      // eslint-disable-next-line no-console
      console.groupCollapsed(`[http] ${res.status} ${path}`);
      // eslint-disable-next-line no-console
      console.error('HTTP error response (parsed JSON):', maybeJson);
      // eslint-disable-next-line no-console
      console.warn('Response headers:', Array.from(res.headers.entries()));
      // eslint-disable-next-line no-console
      console.groupEnd();
    } catch (e) {
      // not JSON
      // eslint-disable-next-line no-console
      console.groupCollapsed(`[http] ${res.status} ${path}`);
      // eslint-disable-next-line no-console
      console.error('HTTP error response (text):', text);
      // eslint-disable-next-line no-console
      console.warn('Response headers:', Array.from(res.headers.entries()));
      // eslint-disable-next-line no-console
      console.groupEnd();
    }
  }
  throw new Error(`[${res.status}] ${path} ${text}`);
}

/**
 * GET 請求（自動附加 Auth 標頭）
 */
export async function getJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const authHeaders = getAuthHeaders();
  const mergedInit: RequestInit = {
    ...init,
    headers: {
      ...authHeaders,
      ...init?.headers,
    },
    cache: "no-store",
  };

  const res = await fetch(buildUrl(path), mergedInit);
  if (!res.ok) {
    return handleNonOk(res, path);
  }
  return res.json() as Promise<T>;
}

/**
 * POST JSON 請求（自動附加 Auth 標頭）
 */
export async function postJSON<T>(
  path: string,
  data: unknown, 
  init?: RequestInit
): Promise<T> {
  const authHeaders = getAuthHeaders();
  
  const postInit: RequestInit = {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders,
    },
    body: JSON.stringify(data),
    cache: 'no-store', 
  };
  
  const mergedInit = { ...postInit, ...init };
  mergedInit.headers = { ...postInit.headers, ...init?.headers };

  const res = await fetch(buildUrl(path), mergedInit);
  if (!res.ok) {
    return handleNonOk(res, path);
  }

  if (res.status === 204 || !res.headers.get("content-type")?.includes("application/json")) {
    return {} as T; 
  }

  return res.json() as Promise<T>;
}

/**
 * POST Form 請求（自動附加 Auth 標頭）
 */
export async function postForm<T>(
  path: string, 
  form: Record<string, string>, 
  init?: RequestInit
): Promise<T> {
  const authHeaders = getAuthHeaders();
  
  const formInit: RequestInit = {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      ...authHeaders,
    },
    body: new URLSearchParams(form),
    cache: 'no-store',
  };
  
  const mergedInit = { ...formInit, ...init };
  mergedInit.headers = { ...formInit.headers, ...init?.headers };

  const res = await fetch(buildUrl(path), mergedInit);
  if (!res.ok) {
    return handleNonOk(res, path);
  }
  return res.json() as Promise<T>;
}

/**
 * PATCH JSON 請求（自動附加 Auth 標頭）
 */
export async function patchJSON<T>(
  path: string,
  data: unknown, 
  init?: RequestInit
): Promise<T> {
  const authHeaders = getAuthHeaders();
  
  const patchInit: RequestInit = {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders,
    },
    body: JSON.stringify(data),
    cache: 'no-store', 
  };
  
  const mergedInit = { ...patchInit, ...init };
  mergedInit.headers = { ...patchInit.headers, ...init?.headers };

  const res = await fetch(buildUrl(path), mergedInit);
  if (!res.ok) {
    return handleNonOk(res, path);
  }

  if (res.status === 204 || !res.headers.get("content-type")?.includes("application/json")) {
    return {} as T; 
  }

  return res.json() as Promise<T>;
}

/**
 * PUT JSON 請求（自動附加 Auth 標頭）
 */
export async function putJSON<T>(
  path: string,
  data: unknown, 
  init?: RequestInit
): Promise<T> {
  const authHeaders = getAuthHeaders();
  
  const putInit: RequestInit = {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders,
    },
    body: JSON.stringify(data),
    cache: 'no-store', 
  };
  
  const mergedInit = { ...putInit, ...init };
  mergedInit.headers = { ...putInit.headers, ...init?.headers };

  const res = await fetch(buildUrl(path), mergedInit);

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`[${res.status}] ${path} ${text}`);
  }
  
  if (res.status === 204 || !res.headers.get("content-type")?.includes("application/json")) {
    return {} as T; 
  }

  return res.json() as Promise<T>;
}

/**
 * DELETE 請求（自動附加 Auth 標頭）
 */
export async function deleteJSON(
  path: string,
  init?: RequestInit
): Promise<void> {
  const authHeaders = getAuthHeaders();
  
  const deleteInit: RequestInit = {
    method: 'DELETE',
    headers: {
      ...authHeaders,
      ...init?.headers,
    },
    cache: 'no-store', 
  };
  
  const mergedInit = { ...deleteInit, ...init };

  const res = await fetch(buildUrl(path), mergedInit);
  if (!res.ok) {
    return handleNonOk(res, path);
  }
  // DELETE 通常回傳 204 No Content，不需要解析 JSON
}
