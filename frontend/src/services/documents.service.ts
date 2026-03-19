import { ApiService } from './api'
import { useAuthStore } from '../store/auth.store'
import type { Document } from '../types'

const API_URL = import.meta.env.VITE_API_URL

function getToken(): string | null {
  return useAuthStore.getState().token
}

export const documentsService = {
  async getDocuments(): Promise<Document[]> {
    return ApiService.get<Document[]>('/api/documents', getToken())
  },

  async uploadDocuments(files: File[]): Promise<Document[]> {
    const token = getToken()
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
    return ApiService.delete<void>(`/api/documents/${id}`, getToken())
  },
}
