import { ApiService } from './api'
import type { SignInResponse } from '../types'

export const authService = {
  async signIn(email: string, password: string): Promise<SignInResponse> {
    return ApiService.post<SignInResponse>('/api/sign-in', { email, password })
  },

  async signUp(email: string, password: string): Promise<SignInResponse> {
    return ApiService.post<SignInResponse>('/api/sign-up', { email, password })
  },
}
