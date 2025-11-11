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
    const text = await res.text().catch(() => "");
    throw new Error(`[${res.status}] ${path} ${text}`);
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
    const text = await res.text().catch(() => "");
    throw new Error(`[${res.status}] ${path} ${text}`);
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
    const text = await res.text().catch(() => "");
    throw new Error(`[${res.status}] ${path} ${text}`);
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
    const text = await res.text().catch(() => "");
    throw new Error(`[${res.status}] ${path} ${text}`);
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
    const text = await res.text().catch(() => "");
    throw new Error(`[${res.status}] ${path} ${text}`);
  }
  
  // DELETE 通常回傳 204 No Content，不需要解析 JSON
}
