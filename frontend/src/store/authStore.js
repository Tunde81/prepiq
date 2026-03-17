import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '../utils/api'

const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (email, password) => {
        const form = new FormData()
        form.append('username', email)
        form.append('password', password)
        const res = await api.post('/auth/login', form, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })
        const { access_token, user } = res.data
        set({ user, token: access_token, isAuthenticated: true })
        api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
        return user
      },

      register: async (email, password, fullName) => {
        await api.post('/auth/register', { email, password, full_name: fullName })
      },

      logout: () => {
        delete api.defaults.headers.common['Authorization']
        set({ user: null, token: null, isAuthenticated: false })
      },

      initAuth: () => {
        const { token } = get()
        if (token) {
          api.defaults.headers.common['Authorization'] = `Bearer ${token}`
        }
      },

      refreshUser: async () => {
        try {
          const res = await api.get('/auth/me')
          set({ user: res.data })
        } catch {
          get().logout()
        }
      }
    }),
    {
      name: 'prepiq-auth',
      partialize: (state) => ({ user: state.user, token: state.token, isAuthenticated: state.isAuthenticated }),
    }
  )
)

export default useAuthStore
