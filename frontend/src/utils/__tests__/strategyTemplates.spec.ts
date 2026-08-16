import { describe, expect, it } from 'vitest'
import { STRATEGY_TEMPLATES } from '../strategyTemplates'

describe('strategyTemplates', () => {
  it('模板数量大于 0 且每个有名称与描述', () => {
    expect(STRATEGY_TEMPLATES.length).toBeGreaterThan(0)
    for (const t of STRATEGY_TEMPLATES) {
      expect(t.name).toBeTruthy()
      expect(t.description).toBeTruthy()
    }
  })

  it('每个模板至少有一个启用的买入信号', () => {
    for (const t of STRATEGY_TEMPLATES) {
      const hasBuy = Object.values(t.config.buy).some((c) => c.enabled)
      expect(hasBuy).toBe(true)
    }
  })

  it('每个模板至少有一个启用的卖出信号', () => {
    for (const t of STRATEGY_TEMPLATES) {
      const hasSell = Object.values(t.config.sell).some((c) => c.enabled)
      expect(hasSell).toBe(true)
    }
  })

  it('每个模板风控参数完整且为正数', () => {
    for (const t of STRATEGY_TEMPLATES) {
      expect(t.config.risk.maxPositionPercent).toBeGreaterThan(0)
      expect(t.config.risk.maxHoldings).toBeGreaterThan(0)
      expect(t.config.risk.maxSingleLoss).toBeGreaterThan(0)
      expect(t.config.risk.totalStopLoss).toBeGreaterThan(0)
      expect(t.config.risk.maxDrawdown).toBeGreaterThan(0)
    }
  })

  it('模板 key 唯一', () => {
    const keys = STRATEGY_TEMPLATES.map((t) => t.key)
    expect(new Set(keys).size).toBe(keys.length)
  })
})
