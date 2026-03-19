import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { AuthStore } from '../types'

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      token: null,
      isLoggedIn: false,
      login: (token: string) => set({ token, isLoggedIn: true }),
      logout: () => set({ token: null, isLoggedIn: false }),
    }),
    {
      name: 'smyp-auth',
      partialize: (state) => ({ token: state.token }),
      onRehydrateStorage: () => (state) => {
        if (!state) return

        if (state.token) {
          state.login(state.token)
          return
        }

        state.logout()
      },
    }
  )
)
