import type { Bar } from '../api'

export interface SupportResistance {
  price: number
  touches: number
  type: 'support' | 'resistance'
}

export interface PatternResult {
  type: string
  label: string
  startIdx: number
  endIdx: number
  level?: number
}

interface PeakValley {
  idx: number
  price: number
  type: 'peak' | 'valley'
}

function findPeaksValleys(bars: Bar[], lookback: number = 5): PeakValley[] {
  const pvs: PeakValley[] = []
  for (let i = lookback; i < bars.length - lookback; i++) {
    const left = bars.slice(i - lookback, i)
    const right = bars.slice(i + 1, i + lookback + 1)
    const curHigh = bars[i].high
    const curLow = bars[i].low
    
    const isPeak = left.every(b => b.high <= curHigh) && right.every(b => b.high <= curHigh)
    const isValley = left.every(b => b.low >= curLow) && right.every(b => b.low >= curLow)
    
    if (isPeak) pvs.push({ idx: i, price: curHigh, type: 'peak' })
    if (isValley) pvs.push({ idx: i, price: curLow, type: 'valley' })
  }
  return pvs
}

function priceMatch(a: number, b: number, tolerance: number = 0.03): boolean {
  return Math.abs(a - b) / Math.max(Math.abs(a), Math.abs(b), 1) < tolerance
}

export function findSupportResistance(bars: Bar[]): SupportResistance[] {
  const pvs = findPeaksValleys(bars)
  const levels: Map<number, { touches: number; type: 'support' | 'resistance' }> = new Map()
  
  for (const pv of pvs) {
    let matched = false
    for (const [price, data] of levels) {
      if (priceMatch(price, pv.price)) {
        levels.set(price, { ...data, touches: data.touches + 1 })
        matched = true
        break
      }
    }
    if (!matched) {
      levels.set(pv.price, { touches: 1, type: pv.type === 'peak' ? 'resistance' : 'support' })
    }
  }
  
  return Array.from(levels.entries())
    .filter(([, d]) => d.touches >= 2)
    .sort((a, b) => b[1].touches - a[1].touches)
    .map(([price, d]) => ({ price, touches: d.touches, type: d.type }))
    .slice(0, 6)
}

export function detectPatterns(bars: Bar[]): PatternResult[] {
  if (bars.length < 40) return []
  const patterns: PatternResult[] = []
  const pvs = findPeaksValleys(bars, 4)
  
  const peaks = pvs.filter(p => p.type === 'peak')
  const valleys = pvs.filter(p => p.type === 'valley')
  
  // 双顶
  for (let i = 0; i < peaks.length - 2; i++) {
    const p1 = peaks[i]
    const p2 = peaks[i + 1]
    if (p2.idx - p1.idx < 30 && priceMatch(p1.price, p2.price) && p2.price > bars[Math.floor((p1.idx + p2.idx) / 2)].low) {
      patterns.push({ type: 'doubleTop', label: '双顶', startIdx: p1.idx, endIdx: p2.idx, level: (p1.price + p2.price) / 2 })
    }
  }
  
  // 双底
  for (let i = 0; i < valleys.length - 2; i++) {
    const v1 = valleys[i]
    const v2 = valleys[i + 1]
    if (v2.idx - v1.idx < 30 && priceMatch(v1.price, v2.price) && v2.price < bars[Math.floor((v1.idx + v2.idx) / 2)].high) {
      patterns.push({ type: 'doubleBottom', label: '双底', startIdx: v1.idx, endIdx: v2.idx, level: (v1.price + v2.price) / 2 })
    }
  }
  
  // 头肩顶
  for (let i = 0; i < peaks.length - 4; i++) {
    const ls = peaks[i]
    const hd = peaks[i + 1]
    const rs = peaks[i + 2]
    if (hd.price > ls.price && hd.price > rs.price && priceMatch(ls.price, rs.price) 
        && hd.idx - ls.idx < 30 && rs.idx - hd.idx < 30) {
      patterns.push({ type: 'headShouldersTop', label: '头肩顶', startIdx: ls.idx, endIdx: rs.idx, level: (ls.price + rs.price) / 2 })
    }
  }
  
  // 上升三角形
  for (let i = 0; i < peaks.length - 2; i++) {
    const p1 = peaks[i]
    const p2 = peaks[i + 2]
    const v1 = valleys[i]
    const v2 = valleys[i + 2]
    if (p2.price >= p1.price * 0.98 && v2.price > v1.price && priceMatch(p1.price, p2.price)) {
      patterns.push({ type: 'ascendingTriangle', label: '上升三角', startIdx: v1.idx, endIdx: p2.idx, level: p1.price })
    }
  }
  
  return patterns
}