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
  up: '#e0393e',
  down: '#0aa869',
  line: '#1a73e8',
  text: '#303133',
  text2: '#909399',
  grid: '#c0c4cc',
  bg: '#ffffff',
  border: '#e0e0e0',
  upFill: 'rgba(224, 57, 62, 0.12)',
  downFill: 'rgba(10, 168, 105, 0.12)',
  ma1: '#f5a623',
  ma2: '#409eff',
  ma3: '#9254de',
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
