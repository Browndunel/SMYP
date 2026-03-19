import { useRef, useState, type DragEvent } from 'react'
import { CloudUpload } from 'lucide-react'

interface DropZoneProps {
  onFiles: (files: File[]) => void
  onClick?: () => void
  disabled?: boolean
  compact?: boolean
}

const ACCEPTED_TYPES = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg']

export function DropZone({ onFiles, onClick, disabled, compact }: DropZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
    if (disabled) return
    const files = Array.from(e.dataTransfer.files).filter((f) => ACCEPTED_TYPES.includes(f.type))
    if (files.length > 0) onFiles(files)
  }

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    if (!disabled) setIsDragging(true)
  }

  const handleDragLeave = () => setIsDragging(false)

  const handleClick = () => {
    if (disabled) return
    if (onClick) {
      onClick()
    } else {
      inputRef.current?.click()
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? [])
    if (files.length > 0) onFiles(files)
    e.target.value = ''
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={handleClick}
      className={[
        'relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed transition-colors cursor-pointer select-none',
        compact ? 'py-6 gap-2' : 'py-16 gap-3',
        isDragging
          ? 'border-primary bg-accent/50'
          : 'border-border hover:border-primary/50 hover:bg-muted/50',
        disabled ? 'opacity-50 cursor-not-allowed' : '',
      ].join(' ')}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".pdf,.jpg,.jpeg,.png"
        className="hidden"
        onChange={handleChange}
        disabled={disabled}
      />
      <div className={[
        'rounded-full bg-accent flex items-center justify-center',
        compact ? 'w-10 h-10' : 'w-14 h-14',
      ].join(' ')}>
        <CloudUpload className="text-primary" size={compact ? 20 : 26} />
      </div>
      <div className="text-center">
        <p className={['font-medium tracking-[-0.02em] text-foreground', compact ? 'text-sm' : 'text-base'].join(' ')}>
          Glissez vos fichiers ici
        </p>
        <p className="text-xs text-muted-foreground mt-0.5">
          PDF, JPG, PNG — cliquez pour sélectionner
        </p>
      </div>
    </div>
  )
}
