import { describe, expect, it } from 'vitest'
import { isMainBoard, isBlockedBoard } from '../board'

describe('board', () => {
  it('isMainBoard 识别沪深主板', () => {
    expect(isMainBoard('600000')).toBe(true)
    expect(isMainBoard('601318')).toBe(true)
    expect(isMainBoard('000001')).toBe(true)
    expect(isMainBoard('002594')).toBe(true)
  })

  it('isMainBoard 排除创业板与科创板', () => {
    expect(isMainBoard('300750')).toBe(false)
    expect(isMainBoard('301236')).toBe(false)
    expect(isMainBoard('688981')).toBe(false)
    expect(isMainBoard('689009')).toBe(false)
  })

  it('isMainBoard 排除非法格式', () => {
    expect(isMainBoard('60000')).toBe(false)
    expect(isMainBoard('abc')).toBe(false)
    expect(isMainBoard('')).toBe(false)
  })

  it('isBlockedBoard 识别创业板与科创板', () => {
    expect(isBlockedBoard('300750')).toBe(true)
    expect(isBlockedBoard('301236')).toBe(true)
    expect(isBlockedBoard('688981')).toBe(true)
    expect(isBlockedBoard('689009')).toBe(true)
  })

  it('isBlockedBoard 主板与非法格式均非禁止板块', () => {
    expect(isBlockedBoard('600000')).toBe(false)
    expect(isBlockedBoard('000001')).toBe(false)
    expect(isBlockedBoard('300')).toBe(false)
    expect(isBlockedBoard('xyz')).toBe(false)
  })
})
