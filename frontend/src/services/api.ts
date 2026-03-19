const API_URL = import.meta.env.VITE_API_URL

const getHeaders = (token?: string | null): Record<string, string> => {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`
  return headers
}

const handleResponse = async <T>(response: Response): Promise<T> => {
  const data = await response.json()
  if (!response.ok) throw data
  return data as T
}

export const ApiService = {
  get: async <T>(path: string, token?: string | null): Promise<T> => {
    const res = await fetch(`${API_URL}${path}`, { headers: getHeaders(token) })
    return handleResponse<T>(res)
  },

  post: async <T>(path: string, body: unknown, token?: string | null): Promise<T> => {
    const res = await fetch(`${API_URL}${path}`, {
      method: 'POST',
      headers: getHeaders(token),
      body: JSON.stringify(body),
    })
    return handleResponse<T>(res)
  },

  patch: async <T>(path: string, body: unknown, token?: string | null): Promise<T> => {
    const res = await fetch(`${API_URL}${path}`, {
      method: 'PATCH',
      headers: getHeaders(token),
      body: JSON.stringify(body),
    })
    return handleResponse<T>(res)
  },

  delete: async <T>(path: string, token?: string | null): Promise<T> => {
    const res = await fetch(`${API_URL}${path}`, {
      method: 'DELETE',
      headers: getHeaders(token),
    })
    return handleResponse<T>(res)
  },
}
