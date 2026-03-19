import { api } from './api'
import type { SignInResponse } from '../types'

export const authService = {
  async signIn(email: string, password: string): Promise<SignInResponse> {
    const { data } = await api.post<SignInResponse>('/api/sign-in', { email, password })
    return data
  },

  async signUp(email: string, password: string): Promise<SignInResponse> {
    const { data } = await api.post<SignInResponse>('/api/sign-up', { email, password })
    return data
  },
}
