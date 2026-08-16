import { defineStore } from 'pinia'
import { accountApi } from '../api'
import type { AccountEquityPoint } from '../api'
import type { Account } from '../api/types'

export const useAccountStore = defineStore('account', {
  state: () => ({
    account: null as Account | null,
    equity: [] as AccountEquityPoint[],
    loading: false,
    error: '',
  }),
  getters: {
    brokerType: (s) => s.account?.broker_type ?? 'paper',
    isLive: (s) => s.account?.broker_type === 'live',
  },
  actions: {
    async fetch() {
      this.loading = true
      this.error = ''
      try {
        this.account = await accountApi.get()
      } catch (e) {
        this.error = (e as Error).message
      } finally {
        this.loading = false
      }
    },
    async fetchEquity() {
      try {
        this.equity = await accountApi.equity()
      } catch (e) {
        this.error = (e as Error).message
      }
    },
    async reset() {
      this.error = ''
      await accountApi.reset()
      await this.fetch()
    },
  },
})
