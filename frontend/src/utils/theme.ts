export interface ChartColors {
  up: string
  down: string
  line: string
  text: string
  text2: string
  grid: string
  bg: string
  border: string
  upFill: string
  downFill: string
  ma1: string
  ma2: string
  ma3: string
}

const FALLBACK: ChartColors = {
  up: '#dc2626',
  down: '#16a34a',
  line: '#2563eb',
  text: '#111827',
  text2: '#6b7280',
  grid: '#e5e7eb',
  bg: '#ffffff',
  border: '#e5e7eb',
  upFill: 'rgba(220, 38, 38, 0.08)',
  downFill: 'rgba(22, 163, 74, 0.08)',
  ma1: '#f59e0b',
  ma2: '#3b82f6',
  ma3: '#8b5cf6',
}

export function chartColors(): ChartColors {
  if (typeof document === 'undefined') return FALLBACK
  const cs = getComputedStyle(document.documentElement)
  return {
    up: cs.getPropertyValue('--up').trim() || FALLBACK.up,
    down: cs.getPropertyValue('--down').trim() || FALLBACK.down,
    line: cs.getPropertyValue('--primary').trim() || FALLBACK.line,
    text: cs.getPropertyValue('--text').trim() || FALLBACK.text,
    text2: cs.getPropertyValue('--text-2').trim() || FALLBACK.text2,
    grid: cs.getPropertyValue('--border').trim() || FALLBACK.grid,
    bg: cs.getPropertyValue('--card').trim() || FALLBACK.bg,
    border: cs.getPropertyValue('--border').trim() || FALLBACK.border,
    upFill: cs.getPropertyValue('--up-bg').trim() || FALLBACK.upFill,
    downFill: cs.getPropertyValue('--down-bg').trim() || FALLBACK.downFill,
    ma1: cs.getPropertyValue('--ma1').trim() || FALLBACK.ma1,
    ma2: cs.getPropertyValue('--ma2').trim() || FALLBACK.ma2,
    ma3: cs.getPropertyValue('--ma3').trim() || FALLBACK.ma3,
  }
}
