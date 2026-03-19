import { useState } from 'react'
import { useAuthStore } from '../store/auth.store'
import { authService } from '../services/auth.service'

function extractMessage(err: unknown, fallback: string): string {
  if (typeof err === 'object' && err !== null && 'message' in err) {
    return String((err as Record<string, unknown>).message)
  }
  return fallback
}

export function useAuth() {
  const { token, isLoggedIn, login, logout } = useAuthStore()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const signIn = async (email: string, password: string): Promise<boolean> => {
    setIsLoading(true)
    setError(null)
    try {
      const { token } = await authService.signIn(email, password)
      login(token)
      return true
    } catch (err) {
      setError(extractMessage(err, 'Identifiants incorrects'))
      return false
    } finally {
      setIsLoading(false)
    }
  }

  const signUp = async (email: string, password: string): Promise<boolean> => {
    setIsLoading(true)
    setError(null)
    try {
      const { token } = await authService.signUp(email, password)
      login(token)
      return true
    } catch (err) {
      setError(extractMessage(err, 'Erreur lors de la création du compte'))
      return false
    } finally {
      setIsLoading(false)
    }
  }

  return { token, isLoggedIn, isLoading, error, signIn, signUp, logout, clearError: () => setError(null) }
}
