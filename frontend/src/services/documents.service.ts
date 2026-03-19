import { API_URL, ApiService } from './api'
import { useAuthStore } from '../store/auth.store'
import type { Document } from '../types'

function requireToken(): string {
  const { token, logout } = useAuthStore.getState()

  if (!token) {
    logout()
    throw new Error('Session invalide, reconnectez-vous')
  }

  return token
}

export const documentsService = {
  async getDocuments(): Promise<Document[]> {
    return ApiService.get<Document[]>('/api/documents', requireToken())
  },

  async uploadDocuments(files: File[]): Promise<Document[]> {
    const token = requireToken()
    const results: Document[] = []
    for (const file of files) {
      const formData = new FormData()
      formData.append('uploadedDocument', file)
      const headers: Record<string, string> = {}
      if (token) headers['Authorization'] = `Bearer ${token}`
      const res = await fetch(`${API_URL}/api/upload`, {
        method: 'POST',
        headers,
        body: formData,
      })
      const data = await res.json()
      if (!res.ok) throw data
      results.push(data as Document)
    }
    return results
  },

  async deleteDocument(id: string): Promise<void> {
    return ApiService.delete<void>(`/api/documents/${id}`, requireToken())
  },
}
