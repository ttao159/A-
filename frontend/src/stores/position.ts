import { defineStore } from 'pinia'
import { positionApi } from '../api'
import type { Position } from '../api/types'

export const usePositionStore = defineStore('position', {
  state: () => ({
    positions: [] as Position[],
    loading: false,
    error: '',
  }),
  actions: {
    async fetch() {
      this.loading = true
      this.error = ''
      try {
        this.positions = await positionApi.list()
      } catch (e) {
        this.error = (e as Error).message
      } finally {
        this.loading = false
      }
    },
  },
})
