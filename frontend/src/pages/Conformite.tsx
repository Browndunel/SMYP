import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircle2, AlertTriangle, XCircle, AlertCircle } from 'lucide-react'
import { Sidebar } from '../components/layout/Sidebar'
import { Badge } from '../components/ui/Badge'
import { Modal } from '../components/ui/Modal'
import { DropZone } from '../components/upload/DropZone'
import { FileList } from '../components/upload/FileList'
import { Button } from '../components/ui/Button'
import { useDocuments } from '../hooks/useDocuments'
import { useUpload } from '../hooks/useUpload'
import { useAuthStore } from '../store/auth.store'
import { useState } from 'react'
import type { Document } from '../types'

type Filter = 'all' | 'OK' | 'suspect' | 'frauduleux'

export default function Conformite() {
  const navigate = useNavigate()
  const { isLoggedIn } = useAuthStore()
  const { documents, isLoading, fetchDocuments } = useDocuments()
  const { files, isUploading, error: uploadError, addFiles, removeFile, upload } = useUpload()
  const [filter, setFilter] = useState<Filter>('all')
  const [uploadModalOpen, setUploadModalOpen] = useState(false)

  useEffect(() => {
    if (!isLoggedIn) {
      navigate('/')
      return
    }
    fetchDocuments()
  }, [isLoggedIn, navigate, fetchDocuments])

  const ok = documents.filter((d) => d.status === 'OK')
  const suspect = documents.filter((d) => d.status === 'suspect')
  const frauduleux = documents.filter((d) => d.status === 'frauduleux')

  const allAnomalies = documents
    .filter((d) => d.anomalies.length > 0)
    .flatMap((d) =>
      d.anomalies.map((anomaly) => ({ document: d, anomaly }))
    )

  const filtered: Document[] =
    filter === 'all' ? documents : documents.filter((d) => d.status === filter)

  const handleUpload = async () => {
    const ok = await upload()
    if (ok) {
      setUploadModalOpen(false)
      await fetchDocuments()
    }
  }

  const counters = [
    {
      label: 'Conformes',
      count: ok.length,
      icon: CheckCircle2,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50 border-emerald-200',
      filter: 'OK' as Filter,
    },
    {
      label: 'Suspects',
      count: suspect.length,
      icon: AlertTriangle,
      color: 'text-amber-600',
      bg: 'bg-amber-50 border-amber-200',
      filter: 'suspect' as Filter,
    },
    {
      label: 'Frauduleux',
      count: frauduleux.length,
      icon: XCircle,
      color: 'text-red-600',
      bg: 'bg-red-50 border-red-200',
      filter: 'frauduleux' as Filter,
    },
  ]

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <Sidebar onUploadClick={() => setUploadModalOpen(true)} />

      <main className="flex-1 overflow-y-auto p-6 space-y-6">
        <div>
          <h1 className="text-xl font-medium tracking-[-0.02em] text-foreground">Conformité</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Vue d'ensemble de vos documents
          </p>
        </div>

        {/* Counters */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {counters.map(({ label, count, icon: Icon, color, bg, filter: f }) => (
            <button
              key={f}
              onClick={() => setFilter(filter === f ? 'all' : f)}
              className={[
                'rounded-xl border p-5 text-left transition-all hover:shadow-sm',
                bg,
                filter === f ? 'ring-2 ring-offset-2 ring-current' : '',
              ].join(' ')}
            >
              <div className="flex items-center justify-between">
                <Icon size={18} className={color} />
                <span className={['text-2xl font-medium tracking-[-0.02em]', color].join(' ')}>
                  {count}
                </span>
              </div>
              <p className={['text-[11px] font-medium uppercase tracking-[0.08em] mt-2', color].join(' ')}>
                {label}
              </p>
            </button>
          ))}
        </div>

        {/* Active alerts */}
        {allAnomalies.length > 0 && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
            <div className="flex items-center gap-2 mb-3">
              <AlertCircle size={15} className="text-amber-600" />
              <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-amber-700">
                {allAnomalies.length} alerte{allAnomalies.length > 1 ? 's' : ''} active{allAnomalies.length > 1 ? 's' : ''}
              </p>
            </div>
            <div className="space-y-2">
              {allAnomalies.map(({ document, anomaly }, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 rounded-lg bg-white/60 border border-amber-100 px-3 py-2"
                >
                  <Badge
                    variant={document.status === 'frauduleux' ? 'frauduleux' : 'suspect'}
                    className="mt-0.5 flex-shrink-0"
                  >
                    {document.status}
                  </Badge>
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-foreground truncate">{document.name}</p>
                    <p className="text-xs text-amber-700 font-mono mt-0.5">{anomaly}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Filter tabs */}
        <div>
          <div className="flex items-center gap-1 p-1 bg-muted rounded-lg w-fit mb-4">
            {(['all', 'OK', 'suspect', 'frauduleux'] as Filter[]).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={[
                  'px-3 py-1.5 rounded-md text-xs cursor-pointer font-medium transition-colors',
                  filter === f
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground',
                ].join(' ')}
              >
                {f === 'all' ? 'Tous' : f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>

          {isLoading && (
            <div className="flex items-center justify-center py-10">
              <div className="w-5 h-5 rounded-full border-2 border-primary border-t-transparent animate-spin" />
            </div>
          )}

          {!isLoading && filtered.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-10">
              Aucun document {filter !== 'all' ? `"${filter}"` : ''}
            </p>
          )}

          <div className="space-y-2">
            {filtered.map((doc) => {
              const statusVariant = doc.status === 'OK'
                ? 'ok'
                : doc.status === 'suspect'
                ? 'suspect'
                : 'frauduleux'
              return (
                <div
                  key={doc.id}
                  className="flex items-center gap-4 rounded-lg border border-border bg-card px-4 py-3"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">{doc.name}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{doc.date}</p>
                  </div>
                  {doc.anomalies.length > 0 && (
                    <span className="text-xs text-muted-foreground">
                      {doc.anomalies.length} anomalie{doc.anomalies.length > 1 ? 's' : ''}
                    </span>
                  )}
                  <Badge variant={statusVariant}>{doc.status}</Badge>
                </div>
              )
            })}
          </div>
        </div>
      </main>

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
