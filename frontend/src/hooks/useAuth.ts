import { useState } from 'react'
import { useAuthStore } from '../store/auth.store'
import { authService } from '../services/auth.service'
import axios from 'axios'

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
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.message ?? 'Identifiants incorrects')
      } else {
        setError('Une erreur est survenue')
      }
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
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.message ?? 'Erreur lors de la création du compte')
      } else {
        setError('Une erreur est survenue')
      }
      return false
    } finally {
      setIsLoading(false)
    }
  }

  return { token, isLoggedIn, isLoading, error, signIn, signUp, logout, clearError: () => setError(null) }
}
