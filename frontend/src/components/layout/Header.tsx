import { Button } from '../ui/Button'
import { useAuthStore } from '../../store/auth.store'

interface HeaderProps {
  onLoginClick: () => void
}

export function Header({ onLoginClick }: HeaderProps) {
  const { isLoggedIn } = useAuthStore()

  return (
    <header className="fixed top-0 left-0 right-0 z-40 h-14 flex items-center justify-between px-6 bg-background/80 backdrop-blur-sm border-b border-border">
      <a href="/" className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center">
          <span className="text-primary-foreground text-xs font-semibold">S</span>
        </div>
        <span className="font-medium tracking-[-0.02em] text-foreground text-sm">SMYP</span>
      </a>

      {!isLoggedIn && (
        <Button variant="secondary" size="sm" onClick={onLoginClick}>
          Se connecter
        </Button>
      )}
    </header>
  )
}
