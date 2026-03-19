import { useState } from 'react'
import { documentsService } from '../services/documents.service'
import { useDocumentsStore } from '../store/documents.store'
import axios from 'axios'

export function useUpload() {
  const [files, setFiles] = useState<File[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { addDocuments } = useDocumentsStore()

  const addFiles = (newFiles: File[]) => {
    setFiles((prev) => {
      const existing = new Set(prev.map((f) => f.name))
      const filtered = newFiles.filter((f) => !existing.has(f.name))
      return [...prev, ...filtered]
    })
  }

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const clearFiles = () => setFiles([])

  const upload = async (): Promise<boolean> => {
    if (files.length === 0) return false
    setIsUploading(true)
    setError(null)
    try {
      const docs = await documentsService.uploadDocuments(files)
      addDocuments(docs)
      setFiles([])
      return true
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.message ?? 'Erreur lors de l\'envoi')
      } else {
        setError('Erreur lors de l\'envoi des documents')
      }
      return false
    } finally {
      setIsUploading(false)
    }
  }

  return { files, isUploading, error, addFiles, removeFile, clearFiles, upload, clearError: () => setError(null) }
}
