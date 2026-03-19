import { type InputHTMLAttributes, forwardRef } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = '', id, ...props }, ref) => {
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={id}
            className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={id}
          className={[
            'h-9 w-full rounded-lg border border-input bg-background px-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-colors disabled:cursor-not-allowed disabled:opacity-50',
            error ? 'border-destructive focus:ring-destructive' : '',
            className,
          ].join(' ')}
          {...props}
        />
        {error && <p className="text-xs text-destructive">{error}</p>}
      </div>
    )
  }
)

Input.displayName = 'Input'
