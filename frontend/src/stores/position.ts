import { defineStore } from 'pinia'
import { positionApi } from '../api'
import type { Position } from '../api/types'
import { loadLS, saveLS } from '../utils/storage'

const CACHE_POSITIONS = 'cache:positions'

export const usePositionStore = defineStore('position', {
  state: () => ({
    positions: loadLS<Position[]>(CACHE_POSITIONS) ?? [],
    loading: false,
    error: '',
  }),
  actions: {
    async fetch() {
      this.loading = true
      this.error = ''
      try {
        this.positions = await positionApi.list()
        saveLS(CACHE_POSITIONS, this.positions)
      } catch (e) {
        this.error = (e as Error).message
      } finally {
        this.loading = false
      }
    },
  },
})
