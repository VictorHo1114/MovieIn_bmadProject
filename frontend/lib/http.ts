import { API_BASE } from "./config";

/**
 * [升級！] 這是一個新的輔助函式
 * 它會自動建立並附加 'Authorization' 標頭 (如果 token 存在)
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

// --- (升級) getJSON ---
export async function getJSON<T>(path: string, init?: RequestInit): Promise<T> {
  // [修改！] 組合 auth 標頭
  const authHeaders = getAuthHeaders();
  const mergedInit: RequestInit = {
    ...init,
    headers: {
      ...authHeaders,
      ...init?.headers,
    },
    cache: "no-store",
  };

  const res = await fetch(`${API_BASE}${path}`, mergedInit); // 使用 mergedInit
  
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`[${res.status}] ${path} ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function postJSON<T>(path: string, body: unknown, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    body: JSON.stringify(body),
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`[${res.status}] ${path} ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function postForm<T>(path: string, form: Record<string, string>, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded", ...(init?.headers ?? {}) },
    body: new URLSearchParams(form),
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`[${res.status}] ${path} ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function postJSON<T>(path: string, body: unknown, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    body: JSON.stringify(body),
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`[${res.status}] ${path} ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function postForm<T>(path: string, form: Record<string, string>, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded", ...(init?.headers ?? {}) },
    body: new URLSearchParams(form),
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`[${res.status}] ${path} ${text}`);
  }
  return res.json() as Promise<T>;
}

// --- (升級) postJSON ---
export async function postJSON<T>(
  path: string,
  data: unknown, 
  init?: RequestInit
): Promise<T> {
  
  // [修改！] 組合 auth 標頭
  const authHeaders = getAuthHeaders();
  
  const postInit: RequestInit = {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders, // <-- 在這裡加入 Auth 標頭
    },
    body: JSON.stringify(data),
    cache: 'no-store', 
  };
  
  const mergedInit = { ...postInit, ...init };
  mergedInit.headers = { ...postInit.headers, ...init?.headers };

  const res = await fetch(`${API_BASE}${path}`, mergedInit); // 使用 mergedInit

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`[${res.status}] ${path} ${text}`);
  }
  
  if (res.status === 204 || !res.headers.get("content-type")?.includes("application/json")) {
    return {} as T; 
  }

  return res.json() as Promise<T>;
}
export async function patchJSON<T>(
  path: string,
  data: unknown, 
  init?: RequestInit
): Promise<T> {
  
  const authHeaders = getAuthHeaders(); // (我們在 http.ts 中已有的函式)
  
  const patchInit: RequestInit = {
    method: 'PATCH', // [關鍵！] 方法是 PATCH
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders,
    },
    body: JSON.stringify(data),
    cache: 'no-store', 
  };
  
  const mergedInit = { ...patchInit, ...init };
  mergedInit.headers = { ...patchInit.headers, ...init?.headers };

  const res = await fetch(`${API_BASE}${path}`, mergedInit);

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`[${res.status}] ${path} ${text}`);
  }
  
  if (res.status === 204 || !res.headers.get("content-type")?.includes("application/json")) {
    return {} as T; 
  }

  return res.json() as Promise<T>;
}