import { describe, expect, it } from 'vitest'
import { compareVersions } from '../version'

describe('version', () => {
  it('比较语义化版本大小', () => {
    expect(compareVersions('0.2.0', '0.1.0')).toBeGreaterThan(0)
    expect(compareVersions('0.1.0', '0.2.0')).toBeLessThan(0)
    expect(compareVersions('0.1.0', '0.1.0')).toBe(0)
  })

  it('长度不一致时按高位对齐比较', () => {
    expect(compareVersions('0.1', '0.1.0')).toBe(0)
    expect(compareVersions('0.10.0', '0.9.0')).toBeGreaterThan(0)
    expect(compareVersions('1.0.0', '0.99.9')).toBeGreaterThan(0)
  })

  it('非法段按 0 处理', () => {
    expect(compareVersions('a.b', '0.0.0')).toBe(0)
  })
})
