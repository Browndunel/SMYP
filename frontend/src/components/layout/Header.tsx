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
        <img src="/SMYP-logo.png" alt="SMYP" className="size-18" />
        <span className="font-medium tracking-[-0.02em] text-foreground text-sm">SMYP - ShareMeYourPaperasse</span>
      </a>

      {!isLoggedIn && (
        <Button variant="secondary" size="sm" onClick={onLoginClick}>
          Se connecter
        </Button>
      )}
    </header>
  )
}
