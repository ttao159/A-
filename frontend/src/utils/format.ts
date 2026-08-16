export function fmtMoney(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '--'
  return v.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
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
