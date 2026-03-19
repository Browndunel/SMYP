import { api } from './api'
import type { Document } from '../types'

export const documentsService = {
  async getDocuments(): Promise<Document[]> {
    const { data } = await api.get<Document[]>('/api/documents')
    return data
  },

  async uploadDocuments(files: File[]): Promise<Document[]> {
    const results: Document[] = []
    for (const file of files) {
      const formData = new FormData()
      formData.append('uploadedDocument', file)
      const { data } = await api.post<Document>('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      results.push(data)
    }
    return results
  },

  async deleteDocument(id: string): Promise<void> {
    await api.delete(`/api/documents/${id}`)
  },
}
