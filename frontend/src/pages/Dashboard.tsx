import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Inbox } from 'lucide-react'
import { Sidebar } from '../components/layout/Sidebar'
import { DocumentCard } from '../components/documents/DocumentCard'
import { DocumentDetail } from '../components/documents/DocumentDetail'
import { DropZone } from '../components/upload/DropZone'
import { FileList } from '../components/upload/FileList'
import { Modal } from '../components/ui/Modal'
import { Button } from '../components/ui/Button'
import { useDocuments } from '../hooks/useDocuments'
import { useUpload } from '../hooks/useUpload'
import { useAuthStore } from '../store/auth.store'
import type { Document } from '../types'

export default function Dashboard() {
  const navigate = useNavigate()
  const { token } = useAuthStore()
  const { documents, isLoading, fetchDocuments, deleteDocument } = useDocuments()
  const { files, isUploading, error: uploadError, addFiles, removeFile, upload } = useUpload()

  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null)
  const [uploadModalOpen, setUploadModalOpen] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) {
      navigate('/')
      return
    }
    fetchDocuments()
  }, [token, navigate, fetchDocuments])

  // Auto-select first document
  useEffect(() => {
    if (!selectedDoc && documents.length > 0) {
      setSelectedDoc(documents[0])
    }
  }, [documents, selectedDoc])

  const handleDelete = async (id: string) => {
    try {
      await deleteDocument(id)
      if (selectedDoc?.id === id) {
        setSelectedDoc(null)
      }
    } catch {
      setDeleteError('Erreur lors de la suppression')
    }
  }

  const handleUpload = async () => {
    const ok = await upload()
    if (ok) {
      setUploadModalOpen(false)
      await fetchDocuments()
    }
  }

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <Sidebar onUploadClick={() => setUploadModalOpen(true)} />

      <div className="flex-1 flex overflow-hidden">
        {/* Document list */}
        <div className="w-72 flex-shrink-0 border-r border-border flex flex-col overflow-hidden">
          <div className="px-4 py-3 border-b border-border flex items-center justify-between">
            <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground">
              Documents
            </p>
            <span className="text-xs text-muted-foreground">{documents.length}</span>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
            {isLoading && (
              <div className="flex items-center justify-center py-10">
                <div className="w-5 h-5 rounded-full border-2 border-primary border-t-transparent animate-spin" />
              </div>
            )}

            {!isLoading && documents.length === 0 && (
              <div className="flex flex-col items-center justify-center py-12 text-center gap-2 px-4">
                <Inbox size={28} className="text-muted-foreground/50" />
                <p className="text-sm text-muted-foreground">Aucun document</p>
                <p className="text-xs text-muted-foreground/70">Uploadez votre premier document</p>
              </div>
            )}

            {documents.map((doc) => (
              <DocumentCard
                key={doc.id}
                document={doc}
                selected={selectedDoc?.id === doc.id}
                onClick={() => setSelectedDoc(doc)}
                onDelete={() => handleDelete(doc.id)}
              />
            ))}
          </div>
        </div>

        {/* Document detail */}
        <div className="flex-1 overflow-y-auto p-6">
          {deleteError && (
            <div className="mb-4 rounded-lg bg-destructive/10 border border-destructive/20 px-4 py-2">
              <p className="text-sm text-destructive">{deleteError}</p>
            </div>
          )}

          {selectedDoc ? (
            <DocumentDetail document={selectedDoc} />
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-muted flex items-center justify-center">
                <Inbox size={20} className="text-muted-foreground" />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">Sélectionnez un document</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Les détails apparaîtront ici
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Upload Modal */}
      <Modal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        title="Uploader des documents"
      >
        <div className="flex flex-col gap-4">
          <DropZone onFiles={addFiles} compact />
          <FileList files={files} onRemove={removeFile} />
          {uploadError && (
            <p className="text-sm text-destructive">{uploadError}</p>
          )}
          <Button
            onClick={handleUpload}
            isLoading={isUploading}
            disabled={files.length === 0}
            className="w-full"
          >
            Envoyer {files.length > 0 ? `${files.length} document${files.length > 1 ? 's' : ''}` : ''}
          </Button>
        </div>
      </Modal>
    </div>
  )
}
