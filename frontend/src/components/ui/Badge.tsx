type BadgeVariant = 'ok' | 'suspect' | 'frauduleux' | 'default'

interface BadgeProps {
  variant?: BadgeVariant
  children: React.ReactNode
  className?: string
}

const variantClasses: Record<BadgeVariant, string> = {
  ok: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  suspect: 'bg-amber-100 text-amber-700 border-amber-200',
  frauduleux: 'bg-red-100 text-red-700 border-red-200',
  default: 'bg-muted text-muted-foreground border-border',
}

export function Badge({ variant = 'default', children, className = '' }: BadgeProps) {
  return (
    <span
      className={[
        'inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium uppercase tracking-[0.06em]',
        variantClasses[variant],
        className,
      ].join(' ')}
    >
      {children}
    </span>
  )
}
