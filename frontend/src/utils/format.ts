export function fmtMoney(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '--'
  return v.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export function fmtMoneyCompact(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '--'
  const abs = Math.abs(v)
  const sign = v < 0 ? '-' : ''
  if (abs >= 100000000) return `${sign}${(abs / 100000000).toFixed(2)}亿`
  if (abs >= 10000) return `${sign}${(abs / 10000).toFixed(2)}万`
  return fmtMoney(v)
}

export function fmtPct(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '--'
  const sign = v > 0 ? '+' : ''
  return `${sign}${v.toFixed(2)}%`
}

export function fmtPrice(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '--'
  return v.toFixed(2)
}

export function fmtDateTime(v: string | null | undefined): string {
  if (!v) return ''
  return v.slice(5, 16).replace('T', ' ')
}

export function pnlClass(v: number | null | undefined): 'up' | 'down' {
  return (v ?? 0) >= 0 ? 'up' : 'down'
}
