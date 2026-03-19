import { FileText, X } from 'lucide-react'

interface FileListProps {
  files: File[]
  onRemove: (index: number) => void
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} o`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} Ko`
  return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`
}

export function FileList({ files, onRemove }: FileListProps) {
  if (files.length === 0) return null

  return (
    <ul className="mt-3 space-y-1.5">
      {files.map((file, i) => (
        <li
          key={`${file.name}-${i}`}
          className="flex items-center gap-3 rounded-lg border border-border bg-card px-3 py-2"
        >
          <FileText size={14} className="text-muted-foreground flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate text-foreground">{file.name}</p>
            <p className="text-xs text-muted-foreground">{formatSize(file.size)}</p>
          </div>
          <button
            onClick={() => onRemove(i)}
            className="text-muted-foreground hover:text-destructive transition-colors p-1 rounded"
          >
            <X size={14} />
          </button>
        </li>
      ))}
    </ul>
  )
}
