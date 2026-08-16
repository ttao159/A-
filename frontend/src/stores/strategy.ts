import { defineStore } from 'pinia'
import { strategyApi } from '../api'
import type { Strategy, StrategyInput } from '../api/types'

export const useStrategyStore = defineStore('strategy', {
  state: () => ({
    strategies: [] as Strategy[],
    loading: false,
    error: '',
  }),
  getters: {
    enabled: (s) => s.strategies.filter((x) => x.enabled),
    byId: (s) => (id: number) => s.strategies.find((x) => x.id === id),
  },
  actions: {
    async fetch() {
      this.loading = true
      this.error = ''
      try {
        this.strategies = await strategyApi.list()
      } catch (e) {
        this.error = (e as Error).message
      } finally {
        this.loading = false
      }
    },
    async create(input: StrategyInput) {
      this.error = ''
      const created = await strategyApi.create(input)
      this.strategies.push(created)
      return created
    },
    async update(id: number, input: StrategyInput) {
      this.error = ''
      const updated = await strategyApi.update(id, input)
      const idx = this.strategies.findIndex((x) => x.id === id)
      if (idx >= 0) this.strategies[idx] = updated
      return updated
    },
    async remove(id: number) {
      this.error = ''
      await strategyApi.remove(id)
      this.strategies = this.strategies.filter((x) => x.id !== id)
    },
  },
})
