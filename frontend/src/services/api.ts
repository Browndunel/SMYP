const DEFAULT_API_URL = 'http://localhost:5000'

export const API_URL = (import.meta.env.VITE_API_URL || DEFAULT_API_URL).replace(/\/$/, '')

const getHeaders = (token?: string | null): Record<string, string> => {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`
  return headers
}

const extractApiErrorMessage = (data: unknown): string => {
  if (typeof data === 'object' && data !== null) {
    if ('message' in data && typeof data.message === 'string') {
      return data.message
    }

    if ('error' in data && typeof data.error === 'string') {
      return data.error
    }
  }

  return 'Une erreur est survenue'
}

const handleResponse = async <T>(response: Response): Promise<T> => {
  const data = await response.json()

  if (!response.ok) {
    throw {
      message: extractApiErrorMessage(data),
      status: response.status,
      data,
    }
  }

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
