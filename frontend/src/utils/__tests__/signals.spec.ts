import { describe, expect, it } from 'vitest'
import { signalName, sigNames, signalParamText } from '../signals'

describe('signals', () => {
  it('signalName 返回买入信号标签', () => {
    expect(signalName('maCross')).toBe('均线金叉')
    expect(signalName('breakHigh')).toBe('突破新高')
  })

  it('signalName 返回卖出信号标签', () => {
    expect(signalName('takeProfit')).toBe('固定止盈')
    expect(signalName('stopLoss')).toBe('固定止损')
  })

  it('signalName 未知 key 回退为自身', () => {
    expect(signalName('unknownKey')).toBe('unknownKey')
  })

  it('sigNames 拼接买卖信号标签', () => {
    expect(sigNames({ buy: ['maCross'], sell: ['takeProfit'] })).toBe('均线金叉 / 固定止盈')
  })

  it('sigNames 空信号返回破折号', () => {
    expect(sigNames({})).toBe('—')
  })

  it('signalParamText 忽略 enabled 并格式化参数', () => {
    expect(signalParamText({ enabled: true, shortPeriod: 5, longPeriod: 20 })).toBe('短周期 5 · 长周期 20')
  })
})
