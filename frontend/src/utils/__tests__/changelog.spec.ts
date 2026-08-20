import { describe, expect, it } from 'vitest'
import { CHANGELOG, NOTICES } from '../changelog'

describe('changelog', () => {
  it('版本日志非空且每条字段完整', () => {
    expect(CHANGELOG.length).toBeGreaterThan(0)
    for (const e of CHANGELOG) {
      expect(e.version).toBeTruthy()
      expect(e.date).toBeTruthy()
      expect(['新增', '优化', '修复', '安全', '移除']).toContain(e.tag)
      expect(e.content).toBeTruthy()
    }
  })

  it('版本日志按日期从新到旧排序', () => {
    for (let i = 1; i < CHANGELOG.length; i++) {
      expect(CHANGELOG[i - 1].date >= CHANGELOG[i].date).toBe(true)
    }
  })

  it('公告非空且等级合法', () => {
    expect(NOTICES.length).toBeGreaterThan(0)
    for (const n of NOTICES) {
      expect(['static', 'warning', 'danger']).toContain(n.level)
      expect(n.title).toBeTruthy()
    }
  })
})
