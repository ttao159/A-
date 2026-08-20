import { defineStore } from 'pinia'
import { accountApi } from '../api'
import type { AccountEquityPoint } from '../api'
import type { Account } from '../api/types'
import { loadLS, saveLS } from '../utils/storage'

const CACHE_ACCOUNT = 'cache:account'
const CACHE_EQUITY = 'cache:equity'

export const useAccountStore = defineStore('account', {
  state: () => ({
    account: loadLS<Account>(CACHE_ACCOUNT),
    equity: loadLS<AccountEquityPoint[]>(CACHE_EQUITY) ?? [],
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
        saveLS(CACHE_ACCOUNT, this.account)
      } catch (e) {
        this.error = (e as Error).message
      } finally {
        this.loading = false
      }
    },
    async fetchEquity() {
      try {
        this.equity = await accountApi.equity()
        saveLS(CACHE_EQUITY, this.equity)
      } catch (e) {
        this.error = (e as Error).message
      }
    },
    setLive(live: boolean) {
      if (!this.account) {
        this.account = {
          broker_type: live ? 'live' : 'paper',
          initial_capital: 1000000,
          available_cash: 1000000,
          market_value: 0,
          total_asset: 1000000,
          total_pnl: 0,
          today_pnl: 0,
        }
      } else {
        this.account.broker_type = live ? 'live' : 'paper'
      }
      saveLS(CACHE_ACCOUNT, this.account)
    },
    async reset() {
      this.error = ''
      await accountApi.reset()
      await this.fetch()
    },
  },
})
