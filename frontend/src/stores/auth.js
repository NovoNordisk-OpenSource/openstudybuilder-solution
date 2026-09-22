import { defineStore } from 'pinia'

import { auth } from '@/plugins/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    userInfo: null,
    displayWelcomeMsg: false,
  }),

  actions: {
    async initialize() {
      const userInfo = await auth.getUserInfo()
      this.userInfo = userInfo
    },
    setWelcomeMsgFlag(value) {
      this.displayWelcomeMsg = value
    },
  },
})
