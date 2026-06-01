const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:17493';

async function readError(response: Response): Promise<Error> {
  const text = await response.text();
  if (!text) return new Error(`HTTP ${response.status}`);
  try {
    const data = JSON.parse(text) as { detail?: unknown };
    if (typeof data.detail === 'string') return new Error(data.detail);
  } catch {
    // Use raw response text below.
  }
  return new Error(text || `HTTP ${response.status}`);
}

export function apiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(apiUrl(path));
  if (!response.ok) throw await readError(response);
  return response.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw await readError(response);
  return response.json() as Promise<T>;
}

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw await readError(response);
  return response.json() as Promise<T>;
}

export async function apiDelete<T>(path: string): Promise<T> {
  const response = await fetch(apiUrl(path), {
    method: 'DELETE',
  });
  if (!response.ok) throw await readError(response);
  return response.json() as Promise<T>;
}

export async function apiUpload<T>(path: string, file: File | Blob, fileName: string): Promise<T> {
  const body = new FormData();
  body.append('file', file, fileName);
  const response = await fetch(apiUrl(path), {
    method: 'POST',
    body,
  });
  if (!response.ok) throw await readError(response);
  return response.json() as Promise<T>;
}
