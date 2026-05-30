import { defineStore } from 'pinia'
import { api } from '../api/client'

// Роли (раздел 2.5.2).
export const ROLE_NAMES = {
  head_coach: 'Главный тренер',
  assistant: 'Ассистент тренера',
  analyst: 'Аналитик',
  player: 'Игрок',
}

export const useAuthStore = defineStore('auth', {
  state: () => ({ user: null }),
  getters: {
    isAuthenticated: (s) => !!s.user,
    isStaff: (s) => s.user && ['head_coach', 'assistant', 'analyst'].includes(s.user.role),
    isHeadCoach: (s) => s.user && s.user.role === 'head_coach',
    isPlayer: (s) => s.user && s.user.role === 'player',
    roleName: (s) => (s.user ? ROLE_NAMES[s.user.role] : ''),
  },
  actions: {
    async login(login, password) {
      const { data } = await api.login(login, password)
      this.user = data
      return data
    },
    async fetchMe() {
      try {
        const { data } = await api.me()
        this.user = data
      } catch {
        this.user = null
      }
    },
    async logout() {
      await api.logout()
      this.user = null
    },
  },
})
