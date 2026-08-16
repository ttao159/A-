import { defineStore } from 'pinia'
import { tradeApi } from '../api'
import type { TradeSummary } from '../api'
import type { Order, Trade } from '../api/types'

const PAGE_SIZE = 20

const emptySummary: TradeSummary = { total: 0, buys: 0, sells: 0, pnl: 0, wins: 0, losses: 0 }

export const useTradeStore = defineStore('trade', {
  state: () => ({
    trades: [] as Trade[],
    orders: [] as Order[],
    tradeTotal: 0,
    orderTotal: 0,
    tradeHasMore: false,
    orderHasMore: false,
    tradeSummary: { ...emptySummary } as TradeSummary,
    loading: false,
    loadingMore: false,
    error: '',
  }),
  actions: {
    async fetchTrades() {
      this.loading = true
      this.error = ''
      try {
        const res = await tradeApi.list(0, PAGE_SIZE)
        this.trades = res.items
        this.tradeTotal = res.total
        this.tradeHasMore = res.has_more
        this.tradeSummary = res.summary
      } catch (e) {
        this.error = (e as Error).message
      } finally {
        this.loading = false
      }
    },
    async fetchMoreTrades() {
      if (this.loadingMore || !this.tradeHasMore) return
      this.loadingMore = true
      try {
        const res = await tradeApi.list(this.trades.length, PAGE_SIZE)
        this.trades = this.trades.concat(res.items)
        this.tradeTotal = res.total
        this.tradeHasMore = res.has_more
        this.tradeSummary = res.summary
      } catch (e) {
        this.error = (e as Error).message
      } finally {
        this.loadingMore = false
      }
    },
    async fetchOrders() {
      this.loading = true
      this.error = ''
      try {
        const res = await tradeApi.orders(0, PAGE_SIZE)
        this.orders = res.items
        this.orderTotal = res.total
        this.orderHasMore = res.has_more
      } catch (e) {
        this.error = (e as Error).message
      } finally {
        this.loading = false
      }
    },
    async fetchMoreOrders() {
      if (this.loadingMore || !this.orderHasMore) return
      this.loadingMore = true
      try {
        const res = await tradeApi.orders(this.orders.length, PAGE_SIZE)
        this.orders = this.orders.concat(res.items)
        this.orderTotal = res.total
        this.orderHasMore = res.has_more
      } catch (e) {
        this.error = (e as Error).message
      } finally {
        this.loadingMore = false
      }
    },
  },
})
