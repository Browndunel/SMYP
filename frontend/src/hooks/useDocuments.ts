import { useCallback } from 'react'
import { useDocumentsStore } from '../store/documents.store'
import { documentsService } from '../services/documents.service'

export function useDocuments() {
  const { documents, isLoading, setDocuments, addDocuments, removeDocument, setLoading } =
    useDocumentsStore()

  const fetchDocuments = useCallback(async (): Promise<void> => {
    setLoading(true)
    try {
      const docs = await documentsService.getDocuments()
      setDocuments(docs)
    } catch (err) {
      console.error('Failed to fetch documents', err)
    } finally {
      setLoading(false)
    }
  }, [setDocuments, setLoading])

  const deleteDocument = useCallback(
    async (id: string): Promise<void> => {
      await documentsService.deleteDocument(id)
      removeDocument(id)
    },
    [removeDocument]
  )

  return { documents, isLoading, fetchDocuments, addDocuments, deleteDocument }
}
