import { ApiService } from './api'
import type { SignInResponse } from '../types'

function normalizeAuthResponse(response: SignInResponse | string): SignInResponse {
  if (typeof response === 'string') {
    return { token: response }
  }

  return response
}

export const authService = {
  async signIn(email: string, password: string): Promise<SignInResponse> {
    const response = await ApiService.post<SignInResponse | string>('/api/sign-in', { email, password })
    return normalizeAuthResponse(response)
  },

  async signUp(email: string, password: string): Promise<SignInResponse> {
    const response = await ApiService.post<SignInResponse | string>('/api/sign-up', { email, password })
    return normalizeAuthResponse(response)
  },
}
