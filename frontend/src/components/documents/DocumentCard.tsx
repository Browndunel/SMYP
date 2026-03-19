import { FileText, Trash2 } from 'lucide-react'
import type { Document } from '../../types'
import { Badge } from '../ui/Badge'

interface DocumentCardProps {
  document: Document
  selected?: boolean
  onClick: () => void
  onDelete: () => void
}

const typeLabels: Record<Document['type'], string> = {
  facture: 'Facture',
  devis: 'Devis',
  attestation_urssaf: 'URSSAF',
  kbis: 'Kbis',
  rib: 'RIB',
  autre: 'Autre',
}

export function DocumentCard({ document, selected, onClick, onDelete }: DocumentCardProps) {
  const statusVariant = document.status === 'OK'
    ? 'ok'
    : document.status === 'suspect'
    ? 'suspect'
    : 'frauduleux'

  return (
    <div
      onClick={onClick}
      className={[
        'flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer border transition-colors group',
        selected
          ? 'bg-accent border-primary/30'
          : 'bg-card border-transparent hover:border-border hover:bg-muted/30',
      ].join(' ')}
    >
      <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center flex-shrink-0">
        <FileText size={14} className="text-muted-foreground" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate text-foreground tracking-[-0.01em]">{document.name}</p>
        <div className="flex items-center gap-1.5 mt-0.5">
          <span className="text-[11px] text-muted-foreground">{typeLabels[document.type]}</span>
          <span className="text-muted-foreground/40">·</span>
          <span className="text-[11px] text-muted-foreground">{document.date}</span>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Badge variant={statusVariant}>{document.status}</Badge>
        <button
          onClick={(e) => {
            e.stopPropagation()
            onDelete()
          }}
          className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-all p-1 rounded"
        >
          <Trash2 size={13} />
        </button>
      </div>
    </div>
  )
}
