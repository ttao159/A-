import { describe, expect, it } from 'vitest'
import { fmtMoney, fmtMoneyCompact, fmtPct, fmtPrice } from '../format'

describe('format', () => {
  it('fmtMoney 对 null/undefined/NaN 返回占位符', () => {
    expect(fmtMoney(null)).toBe('--')
    expect(fmtMoney(undefined)).toBe('--')
    expect(fmtMoney(Number.NaN)).toBe('--')
  })

  it('fmtMoney 保留两位小数', () => {
    expect(fmtMoney(100)).toBe('100.00')
    expect(fmtMoney(1234.5)).toContain('.50')
  })

  it('fmtPct 正数带 + 号、负数带 - 号、零不带', () => {
    expect(fmtPct(5.678)).toBe('+5.68%')
    expect(fmtPct(-3.2)).toBe('-3.20%')
    expect(fmtPct(0)).toBe('0.00%')
  })

  it('fmtPct 对空值返回占位符', () => {
    expect(fmtPct(null)).toBe('--')
    expect(fmtPct(undefined)).toBe('--')
  })

  it('fmtPrice 保留两位小数', () => {
    expect(fmtPrice(10.5)).toBe('10.50')
    expect(fmtPrice(3)).toBe('3.00')
    expect(fmtPrice(null)).toBe('--')
  })

  it('fmtMoneyCompact 对亿/万级金额缩写', () => {
    expect(fmtMoneyCompact(123456789)).toBe('1.23亿')
    expect(fmtMoneyCompact(1234567.89)).toBe('123.46万')
    expect(fmtMoneyCompact(-20000)).toBe('-2.00万')
  })

  it('fmtMoneyCompact 小额回退精确格式', () => {
    expect(fmtMoneyCompact(5000)).toBe('5,000.00')
    expect(fmtMoneyCompact(null)).toBe('--')
    expect(fmtMoneyCompact(Number.NaN)).toBe('--')
  })
})
