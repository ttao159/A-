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
  score: number
  direction?: 'bullish' | 'bearish'
}

interface PeakValley {
  idx: number
  price: number
  type: 'peak' | 'valley'
}

const MIN_SCORE = 0.45
const MATCH_TOLERANCE = 0.03

function findPeaksValleys(bars: Bar[], lookback = 5): PeakValley[] {
  const pvs: PeakValley[] = []
  for (let i = lookback; i < bars.length - lookback; i++) {
    const left = bars.slice(i - lookback, i)
    const right = bars.slice(i + 1, i + lookback + 1)
    const curHigh = bars[i].high
    const curLow = bars[i].low

    const isPeak = left.every((b) => b.high <= curHigh) && right.every((b) => b.high <= curHigh)
    const isValley = left.every((b) => b.low >= curLow) && right.every((b) => b.low >= curLow)

    if (isPeak) pvs.push({ idx: i, price: curHigh, type: 'peak' })
    if (isValley) pvs.push({ idx: i, price: curLow, type: 'valley' })
  }
  return pvs
}

function priceMatch(a: number, b: number, tolerance = MATCH_TOLERANCE): boolean {
  return Math.abs(a - b) / Math.max(Math.abs(a), Math.abs(b), 1) < tolerance
}

function priceMatchScore(a: number, b: number): number {
  const diff = Math.abs(a - b) / Math.max(Math.abs(a), Math.abs(b), 1)
  return Math.max(0, 1 - diff / MATCH_TOLERANCE)
}

function avgVolume(bars: Bar[], start: number, end: number): number {
  let sum = 0
  for (let i = start; i <= end && i < bars.length; i++) {
    sum += bars[i].volume
  }
  return sum / Math.max(1, end - start + 1)
}

function volumeScore(bars: Bar[], leftBase: number[], breakoutRange: number[]): number {
  const breakoutVol = avgVolume(bars, breakoutRange[0], breakoutRange[1])
  const baseVol = avgVolume(bars, leftBase[0], leftBase[1])
  if (baseVol === 0) return 0.5
  const ratio = breakoutVol / baseVol
  if (ratio >= 1.8) return 1
  if (ratio >= 1.3) return 0.7
  if (ratio >= 1.0) return 0.4
  return 0.1
}

function getTrend(bars: Bar[], start: number, end: number): { direction: 'up' | 'down' | 'sideways'; score: number } {
  if (end - start < 10) return { direction: 'sideways', score: 0.3 }

  const closes = bars.slice(start, end + 1).map((b) => b.close)
  const n = closes.length
  const mid = Math.floor(n / 2)
  const first = closes.slice(0, mid).reduce((a, b) => a + b, 0) / mid
  const second = closes.slice(mid).reduce((a, b) => a + b, 0) / (n - mid)

  const pctChange = (second - first) / Math.max(first, 1)
  if (pctChange > 0.03) return { direction: 'up', score: Math.min(1, pctChange * 6) }
  if (pctChange < -0.03) return { direction: 'down', score: Math.min(1, -pctChange * 6) }
  return { direction: 'sideways', score: 0.5 }
}

export function findSupportResistance(bars: Bar[]): SupportResistance[] {
  const pvs = findPeaksValleys(bars)
  const levels: Map<number, { touches: number; type: 'support' | 'resistance' }> = new Map()

  for (const pv of pvs) {
    let matched = false
    for (const [price, data] of levels) {
      if (priceMatch(price, pv.price)) {
        const newType = pv.type === 'peak' ? 'resistance' : 'support'
        levels.set(price, { touches: data.touches + 1, type: newType })
        matched = true
        break
      }
    }
    if (!matched) {
      const t = pv.type === 'peak' ? 'resistance' : 'support'
      levels.set(pv.price, { touches: 1, type: t })
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
  const peaks = pvs.filter((p) => p.type === 'peak')
  const valleys = pvs.filter((p) => p.type === 'valley')

  patterns.push(...detectDoubleTops(bars, peaks))
  patterns.push(...detectDoubleBottoms(bars, valleys))
  patterns.push(...detectHeadShouldersTop(bars, peaks))
  patterns.push(...detectHeadShouldersBottom(bars, valleys))
  patterns.push(...detectAscendingTriangles(bars, peaks, valleys))
  patterns.push(...detectDescendingTriangles(bars, peaks, valleys))
  patterns.push(...detectSymmetricalTriangles(bars, peaks, valleys))
  patterns.push(...detectBullFlags(bars))
  patterns.push(...detectBearFlags(bars))

  return patterns
    .filter((p) => p.score >= MIN_SCORE)
    .sort((a, b) => b.score - a.score)
    .slice(0, 5)
}

function detectDoubleTops(bars: Bar[], peaks: PeakValley[]): PatternResult[] {
  const results: PatternResult[] = []
  for (let i = 0; i < peaks.length - 2; i++) {
    const p1 = peaks[i]
    const p2 = peaks[i + 1]
    const dist = p2.idx - p1.idx
    if (dist > 50 || dist < 8) continue
    if (!priceMatch(p1.price, p2.price)) continue

    const troughIdx = Math.floor((p1.idx + p2.idx) / 2)
    const troughPrice = bars[troughIdx].low
    if (p2.price <= troughPrice) continue

    const trendBefore = getTrend(bars, Math.max(0, p1.idx - 30), p1.idx)
    const baseRange: [number, number] = [Math.max(0, p1.idx - 10), p1.idx]
    const breakRange: [number, number] = [p2.idx, Math.min(bars.length - 1, p2.idx + 10)]
    const volScore = volumeScore(bars, baseRange, breakRange)
    const priceScore = priceMatchScore(p1.price, p2.price)
    const trendScore = trendBefore.direction === 'up' ? 1 : trendBefore.direction === 'sideways' ? 0.6 : 0.3
    const symmetryScore = Math.max(0, 1 - Math.abs(dist - 20) / 30)
    const score = (priceScore * 0.3 + volScore * 0.2 + trendScore * 0.3 + symmetryScore * 0.2)

    results.push({
      type: 'doubleTop',
      label: '双顶',
      startIdx: p1.idx,
      endIdx: p2.idx,
      level: (p1.price + p2.price) / 2,
      score,
      direction: 'bearish',
    })
  }
  return results
}

function detectDoubleBottoms(bars: Bar[], valleys: PeakValley[]): PatternResult[] {
  const results: PatternResult[] = []
  for (let i = 0; i < valleys.length - 2; i++) {
    const v1 = valleys[i]
    const v2 = valleys[i + 1]
    const dist = v2.idx - v1.idx
    if (dist > 50 || dist < 8) continue
    if (!priceMatch(v1.price, v2.price)) continue

    const peakIdx = Math.floor((v1.idx + v2.idx) / 2)
    const peakPrice = bars[peakIdx].high
    if (v2.price >= peakPrice) continue

    const trendBefore = getTrend(bars, Math.max(0, v1.idx - 30), v1.idx)
    const baseRange: [number, number] = [Math.max(0, v1.idx - 10), v1.idx]
    const breakRange: [number, number] = [v2.idx, Math.min(bars.length - 1, v2.idx + 10)]
    const volScore = volumeScore(bars, baseRange, breakRange)
    const priceScore = priceMatchScore(v1.price, v2.price)
    const trendScore = trendBefore.direction === 'down' ? 1 : trendBefore.direction === 'sideways' ? 0.6 : 0.3
    const symmetryScore = Math.max(0, 1 - Math.abs(dist - 20) / 30)
    const score = (priceScore * 0.3 + volScore * 0.2 + trendScore * 0.3 + symmetryScore * 0.2)

    results.push({
      type: 'doubleBottom',
      label: '双底',
      startIdx: v1.idx,
      endIdx: v2.idx,
      level: (v1.price + v2.price) / 2,
      score,
      direction: 'bullish',
    })
  }
  return results
}

function detectHeadShouldersTop(bars: Bar[], peaks: PeakValley[]): PatternResult[] {
  const results: PatternResult[] = []
  for (let i = 0; i < peaks.length - 2; i++) {
    const ls = peaks[i]
    const hd = peaks[i + 1]
    const rs = peaks[i + 2]
    if (hd.price <= ls.price || hd.price <= rs.price) continue
    if (!priceMatch(ls.price, rs.price)) continue
    const leftDist = hd.idx - ls.idx
    const rightDist = rs.idx - hd.idx
    if (leftDist > 30 || rightDist > 30) continue
    if (leftDist < 4 || rightDist < 4) continue

    const leftValley = bars.slice(ls.idx, hd.idx).reduce((m, b) => (b.low < m ? b.low : m), Infinity)
    const rightValley = bars.slice(hd.idx, rs.idx).reduce((m, b) => (b.low < m ? b.low : m), Infinity)
    const neckline = (leftValley + rightValley) / 2

    const trendBefore = getTrend(bars, Math.max(0, ls.idx - 30), ls.idx)
    const baseRange: [number, number] = [Math.max(0, ls.idx - 10), ls.idx]
    const breakRange: [number, number] = [rs.idx, Math.min(bars.length - 1, rs.idx + 10)]
    const volScore = volumeScore(bars, baseRange, breakRange)
    const priceScore = priceMatchScore(ls.price, rs.price)
    const trendScore = trendBefore.direction === 'up' ? 1 : trendBefore.direction === 'sideways' ? 0.6 : 0.3
    const symmetryScore = Math.max(0, 1 - Math.abs(leftDist - rightDist) / 20)
    const headRatio = (hd.price - Math.min(ls.price, rs.price)) / Math.max(Math.min(ls.price, rs.price), 1)
    const headScore = headRatio > 0.03 ? 1 : headRatio > 0.01 ? 0.6 : 0.3
    const score = (priceScore * 0.2 + volScore * 0.15 + trendScore * 0.25 + symmetryScore * 0.2 + headScore * 0.2)

    results.push({
      type: 'headShouldersTop',
      label: '头肩顶',
      startIdx: ls.idx,
      endIdx: rs.idx,
      level: neckline,
      score,
      direction: 'bearish',
    })
  }
  return results
}

function detectHeadShouldersBottom(bars: Bar[], valleys: PeakValley[]): PatternResult[] {
  const results: PatternResult[] = []
  for (let i = 0; i < valleys.length - 2; i++) {
    const ls = valleys[i]
    const hd = valleys[i + 1]
    const rs = valleys[i + 2]
    if (hd.price >= ls.price || hd.price >= rs.price) continue
    if (!priceMatch(ls.price, rs.price)) continue
    const leftDist = hd.idx - ls.idx
    const rightDist = rs.idx - hd.idx
    if (leftDist > 30 || rightDist > 30) continue
    if (leftDist < 4 || rightDist < 4) continue

    const leftPeak = bars.slice(ls.idx, hd.idx).reduce((m, b) => (b.high > m ? b.high : m), -Infinity)
    const rightPeak = bars.slice(hd.idx, rs.idx).reduce((m, b) => (b.high > m ? b.high : m), -Infinity)
    const neckline = (leftPeak + rightPeak) / 2

    const trendBefore = getTrend(bars, Math.max(0, ls.idx - 30), ls.idx)
    const baseRange: [number, number] = [Math.max(0, ls.idx - 10), ls.idx]
    const breakRange: [number, number] = [rs.idx, Math.min(bars.length - 1, rs.idx + 10)]
    const volScore = volumeScore(bars, baseRange, breakRange)
    const priceScore = priceMatchScore(ls.price, rs.price)
    const trendScore = trendBefore.direction === 'down' ? 1 : trendBefore.direction === 'sideways' ? 0.6 : 0.3
    const symmetryScore = Math.max(0, 1 - Math.abs(leftDist - rightDist) / 20)
    const headRatio = (Math.max(ls.price, rs.price) - hd.price) / Math.max(hd.price, 1)
    const headScore = headRatio > 0.03 ? 1 : headRatio > 0.01 ? 0.6 : 0.3
    const score = (priceScore * 0.2 + volScore * 0.15 + trendScore * 0.25 + symmetryScore * 0.2 + headScore * 0.2)

    results.push({
      type: 'headShouldersBottom',
      label: '头肩底',
      startIdx: ls.idx,
      endIdx: rs.idx,
      level: neckline,
      score,
      direction: 'bullish',
    })
  }
  return results
}

function detectAscendingTriangles(
  bars: Bar[],
  peaks: PeakValley[],
  valleys: PeakValley[],
): PatternResult[] {
  const results: PatternResult[] = []
  for (let i = 0; i < peaks.length - 2 && i < valleys.length - 2; i++) {
    const p1 = peaks[i]
    const p2 = peaks[i + 1]
    const v1 = valleys[i]
    const v2 = valleys[i + 1]

    const span = Math.max(p2.idx, v2.idx) - Math.min(p1.idx, v1.idx)
    if (span > 60 || span < 12) continue
    if (p2.price < p1.price * 0.98 || !priceMatch(p1.price, p2.price)) continue
    if (v2.price <= v1.price) continue

    const baseRange: [number, number] = [Math.max(0, p1.idx - 10), p1.idx]
    const breakRange: [number, number] = [p2.idx, Math.min(bars.length - 1, p2.idx + 10)]
    const volScore = volumeScore(bars, baseRange, breakRange)
    const priceScore = priceMatchScore(p1.price, p2.price)
    const slopeScore = Math.min(1, (v2.price - v1.price) / (Math.max(v1.price, 1) * 0.05))
    const score = (priceScore * 0.3 + volScore * 0.2 + slopeScore * 0.5)

    results.push({
      type: 'ascendingTriangle',
      label: '上升三角',
      startIdx: Math.min(v1.idx, p1.idx),
      endIdx: Math.max(v2.idx, p2.idx),
      level: p1.price,
      score,
      direction: 'bullish',
    })
  }
  return results
}

function detectDescendingTriangles(
  bars: Bar[],
  peaks: PeakValley[],
  valleys: PeakValley[],
): PatternResult[] {
  const results: PatternResult[] = []
  for (let i = 0; i < peaks.length - 2 && i < valleys.length - 2; i++) {
    const p1 = peaks[i]
    const p2 = peaks[i + 1]
    const v1 = valleys[i]
    const v2 = valleys[i + 1]

    const span = Math.max(p2.idx, v2.idx) - Math.min(p1.idx, v1.idx)
    if (span > 60 || span < 12) continue
    if (v2.price > v1.price * 1.02 || !priceMatch(v1.price, v2.price)) continue
    if (p2.price >= p1.price) continue

    const baseRange: [number, number] = [Math.max(0, p1.idx - 10), p1.idx]
    const breakRange: [number, number] = [p2.idx, Math.min(bars.length - 1, p2.idx + 10)]
    const volScore = volumeScore(bars, baseRange, breakRange)
    const priceScore = priceMatchScore(v1.price, v2.price)
    const slopeScore = Math.min(1, (p1.price - p2.price) / (Math.max(p2.price, 1) * 0.05))
    const score = (priceScore * 0.3 + volScore * 0.2 + slopeScore * 0.5)

    results.push({
      type: 'descendingTriangle',
      label: '下降三角',
      startIdx: Math.min(v1.idx, p1.idx),
      endIdx: Math.max(v2.idx, p2.idx),
      level: v1.price,
      score,
      direction: 'bearish',
    })
  }
  return results
}

function detectSymmetricalTriangles(
  bars: Bar[],
  peaks: PeakValley[],
  valleys: PeakValley[],
): PatternResult[] {
  const results: PatternResult[] = []
  for (let i = 0; i < peaks.length - 2 && i < valleys.length - 2; i++) {
    const p1 = peaks[i]
    const p2 = peaks[i + 1]
    const v1 = valleys[i]
    const v2 = valleys[i + 1]

    const span = Math.max(p2.idx, v2.idx) - Math.min(p1.idx, v1.idx)
    if (span > 60 || span < 12) continue
    const peakDrop = (p1.price - p2.price) / Math.max(p1.price, 1)
    const valleyRise = (v2.price - v1.price) / Math.max(v1.price, 1)
    if (peakDrop < 0.015 || valleyRise < 0.015) continue
    if (Math.abs(peakDrop - valleyRise) > 0.03) continue

    const baseRange: [number, number] = [Math.max(0, p1.idx - 10), p1.idx]
    const breakRange: [number, number] = [p2.idx, Math.min(bars.length - 1, p2.idx + 10)]
    const volScore = volumeScore(bars, baseRange, breakRange)
    const convergeScore = Math.max(0, 1 - Math.abs(peakDrop - valleyRise) / 0.03)
    const score = (convergeScore * 0.5 + volScore * 0.5)

    results.push({
      type: 'symmetricalTriangle',
      label: '对称三角',
      startIdx: Math.min(v1.idx, p1.idx),
      endIdx: Math.max(v2.idx, p2.idx),
      level: (p1.price + v1.price) / 2,
      score,
      direction: 'bullish',
    })
  }
  return results
}

function detectBullFlags(bars: Bar[]): PatternResult[] {
  const results: PatternResult[] = []
  for (let i = 0; i < bars.length - 15; i++) {
    const poleEnd = i + 8
    if (poleEnd >= bars.length) break
    const poleStartClose = bars[i].close
    const poleEndClose = bars[poleEnd].close
    const polePct = (poleEndClose - poleStartClose) / Math.max(poleStartClose, 1)
    if (polePct < 0.05) continue

    const flagStart = poleEnd + 1
    const flagEnd = Math.min(flagStart + 12, bars.length - 1)
    if (flagEnd - flagStart < 5) continue

    let flagHigh = -Infinity
    let flagLow = Infinity
    for (let j = flagStart; j <= flagEnd; j++) {
      if (bars[j].high > flagHigh) flagHigh = bars[j].high
      if (bars[j].low < flagLow) flagLow = bars[j].low
    }
    if ((flagHigh - flagLow) / Math.max(flagLow, 1) > 0.06) continue

    const poleVol = avgVolume(bars, i, poleEnd)
    const flagVol = avgVolume(bars, flagStart, flagEnd)
    const volDrop = flagVol > 0 ? poleVol / flagVol : 1

    const poleScore = Math.min(1, polePct / 0.15)
    const volScore = volDrop > 1.3 ? 1 : volDrop > 1.0 ? 0.6 : 0.3
    const score = (poleScore * 0.5 + volScore * 0.5)

    results.push({
      type: 'bullFlag',
      label: '看涨旗形',
      startIdx: i,
      endIdx: flagEnd,
      level: flagHigh,
      score,
      direction: 'bullish',
    })
  }
  return results
}

function detectBearFlags(bars: Bar[]): PatternResult[] {
  const results: PatternResult[] = []
  for (let i = 0; i < bars.length - 15; i++) {
    const poleEnd = i + 8
    if (poleEnd >= bars.length) break
    const poleStartClose = bars[i].close
    const poleEndClose = bars[poleEnd].close
    const polePct = (poleEndClose - poleStartClose) / Math.max(poleStartClose, 1)
    if (polePct > -0.05) continue

    const flagStart = poleEnd + 1
    const flagEnd = Math.min(flagStart + 12, bars.length - 1)
    if (flagEnd - flagStart < 5) continue

    let flagHigh = -Infinity
    let flagLow = Infinity
    for (let j = flagStart; j <= flagEnd; j++) {
      if (bars[j].high > flagHigh) flagHigh = bars[j].high
      if (bars[j].low < flagLow) flagLow = bars[j].low
    }
    if ((flagHigh - flagLow) / Math.max(flagLow, 1) > 0.06) continue

    const poleVol = avgVolume(bars, i, poleEnd)
    const flagVol = avgVolume(bars, flagStart, flagEnd)
    const volDrop = flagVol > 0 ? poleVol / flagVol : 1

    const poleScore = Math.min(1, -polePct / 0.15)
    const volScore = volDrop > 1.3 ? 1 : volDrop > 1.0 ? 0.6 : 0.3
    const score = (poleScore * 0.5 + volScore * 0.5)

    results.push({
      type: 'bearFlag',
      label: '看跌旗形',
      startIdx: i,
      endIdx: flagEnd,
      level: flagLow,
      score,
      direction: 'bearish',
    })
  }
  return results
}