const KEY = "sift_api_key";
const URL_KEY = "sift_api_url";

export function apiUrl(): string {
  if (typeof window === "undefined") {
    return process.env.NEXT_PUBLIC_SIFT_API_URL || "http://127.0.0.1:8000";
  }
  return localStorage.getItem(URL_KEY) || process.env.NEXT_PUBLIC_SIFT_API_URL || "http://127.0.0.1:8000";
}

export function setApiUrl(url: string): void {
  localStorage.setItem(URL_KEY, url);
}

export function setApiKey(key: string): void {
  localStorage.setItem(KEY, key);
}

export function getApiKey(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem(KEY) || "";
}

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const key = getApiKey();
  if (key) headers.set("X-Api-Key", key);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return fetch(`${apiUrl()}${path}`, { ...init, headers });
}
