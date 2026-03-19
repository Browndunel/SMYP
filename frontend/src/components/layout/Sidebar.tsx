import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { FileText, ShieldCheck, LogOut, Upload, Menu, X } from 'lucide-react'
import { useAuthStore } from '../../store/auth.store'
import { Button } from '../ui/Button'

interface SidebarProps {
  onUploadClick: () => void
}

const navItems = [
  { label: 'Documents', href: '/dashboard', icon: FileText },
  { label: 'Conformité', href: '/conformite', icon: ShieldCheck },
]

export function Sidebar({ onUploadClick }: SidebarProps) {
  const { logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-4 py-4 border-b border-sidebar-border">
        <div className="w-7 h-7 rounded-lg bg-sidebar-primary flex items-center justify-center flex-shrink-0">
          <span className="text-sidebar-primary-foreground text-xs font-semibold">S</span>
        </div>
        <span className="font-medium tracking-[-0.02em] text-sidebar-foreground text-sm">SMYP</span>
      </div>

      <div className="p-3 border-b border-sidebar-border">
        <Button
          variant="primary"
          size="sm"
          className="w-full"
          onClick={() => {
            onUploadClick()
            setMobileOpen(false)
          }}
        >
          <Upload size={14} />
          Uploader
        </Button>
      </div>

      <nav className="flex-1 p-2 space-y-0.5">
        {navItems.map(({ label, href, icon: Icon }) => {
          const active = location.pathname === href
          return (
            <button
              key={href}
              onClick={() => {
                navigate(href)
                setMobileOpen(false)
              }}
              className={[
                'w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors text-left',
                active
                  ? 'bg-sidebar-accent text-sidebar-primary'
                  : 'text-sidebar-foreground hover:bg-sidebar-accent/50',
              ].join(' ')}
            >
              <Icon size={15} />
              {label}
            </button>
          )
        })}
      </nav>

      <div className="p-2 border-t border-sidebar-border">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors text-left"
        >
          <LogOut size={15} />
          Déconnexion
        </button>
      </div>
    </div>
  )

  return (
    <>
      {/* Mobile toggle */}
      <button
        className="fixed top-3 left-4 z-50 md:hidden p-2 rounded-lg bg-card border border-border shadow-sm"
        onClick={() => setMobileOpen(!mobileOpen)}
      >
        {mobileOpen ? <X size={16} /> : <Menu size={16} />}
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-foreground/20 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile drawer */}
      <aside
        className={[
          'fixed top-0 left-0 z-40 h-full w-60 bg-sidebar border-r border-sidebar-border transition-transform duration-200 md:hidden',
          mobileOpen ? 'translate-x-0' : '-translate-x-full',
        ].join(' ')}
      >
        <SidebarContent />
      </aside>

      {/* Desktop sidebar */}
      <aside className="hidden md:flex flex-col w-60 flex-shrink-0 h-screen sticky top-0 bg-sidebar border-r border-sidebar-border">
        <SidebarContent />
      </aside>
    </>
  )
}
