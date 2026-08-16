export interface ChartColors {
  up: string
  down: string
  line: string
  text2: string
  grid: string
}

export function chartColors(): ChartColors {
  if (typeof document === 'undefined') {
    return { up: '#e0393e', down: '#0aa869', line: '#1a73e8', text2: '#909399', grid: '#c0c4cc' }
  }
  const cs = getComputedStyle(document.documentElement)
  return {
    up: cs.getPropertyValue('--up').trim() || '#e0393e',
    down: cs.getPropertyValue('--down').trim() || '#0aa869',
    line: cs.getPropertyValue('--primary').trim() || '#1a73e8',
    text2: cs.getPropertyValue('--text-2').trim() || '#909399',
    grid: cs.getPropertyValue('--border').trim() || '#c0c4cc',
  }
}
