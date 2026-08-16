import { defineStore } from 'pinia'
import { tradeApi } from '../api'
import type { Order, Trade } from '../api/types'

export const useTradeStore = defineStore('trade', {
  state: () => ({
    trades: [] as Trade[],
    orders: [] as Order[],
    loading: false,
    error: '',
  }),
  actions: {
    async fetchTrades() {
      this.loading = true
      this.error = ''
      try {
        this.trades = await tradeApi.list()
      } catch (e) {
        this.error = (e as Error).message
      } finally {
        this.loading = false
      }
    },
    async fetchOrders() {
      this.loading = true
      this.error = ''
      try {
        this.orders = await tradeApi.orders()
      } catch (e) {
        this.error = (e as Error).message
      } finally {
        this.loading = false
      }
    },
  },
})
