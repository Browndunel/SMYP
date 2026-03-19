import { useEffect, type ReactNode } from 'react'
import { X } from 'lucide-react'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: ReactNode
  className?: string
}

export function Modal({ isOpen, onClose, title, children, className = '' }: ModalProps) {
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    if (isOpen) {
      document.addEventListener('keydown', handleKey)
      document.body.style.overflow = 'hidden'
    }
    return () => {
      document.removeEventListener('keydown', handleKey)
      document.body.style.overflow = ''
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-foreground/20 backdrop-blur-sm"
        onClick={onClose}
      />
      <div
        className={[
          'relative z-10 w-full max-w-md rounded-xl bg-card border border-border shadow-2xl p-6',
          className,
        ].join(' ')}
        onClick={(e) => e.stopPropagation()}
      >
        {(title !== undefined) && (
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-base font-medium tracking-[-0.02em] text-foreground">{title}</h2>
            <button
              onClick={onClose}
              className="text-muted-foreground hover:text-foreground transition-colors rounded-md p-1 hover:bg-muted"
            >
              <X size={16} />
            </button>
          </div>
        )}
        {children}
      </div>
    </div>
  )
}
