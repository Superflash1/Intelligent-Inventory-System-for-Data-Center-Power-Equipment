import { defineStore } from 'pinia'
import { getReminder } from '../api'

export const useAppStore = defineStore('app', {
  state: () => ({
    needSetPassword: false,
    loadingReminder: false
  }),
  actions: {
    async refreshReminder() {
      this.loadingReminder = true
      try {
        const data = await getReminder()
        this.needSetPassword = !!data.need_set_password
      } finally {
        this.loadingReminder = false
      }
    }
  }
})