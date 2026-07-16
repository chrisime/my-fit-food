const BASE = '/api'

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('token') || ''
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...(options?.headers || {}),
    },
  })
  if (res.status === 401) {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('role')
    window.location.href = '/login'
    throw new Error('Sessão expirada')
  }
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `Request failed: ${res.status}`)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export function get<T = any>(url: string) {
  return request<T>(url)
}

export function post<T = any>(url: string, body?: unknown) {
  return request<T>(url, { method: 'POST', body: body != null ? JSON.stringify(body) : undefined })
}

export function put<T = any>(url: string, body?: unknown) {
  return request<T>(url, { method: 'PUT', body: body != null ? JSON.stringify(body) : undefined })
}

export function patch<T = any>(url: string, body?: unknown) {
  return request<T>(url, { method: 'PATCH', body: body != null ? JSON.stringify(body) : undefined })
}

export function del<T = any>(url: string) {
  return request<T>(url, { method: 'DELETE' })
}
