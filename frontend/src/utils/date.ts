function localDate(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export function todayStr(): string {
  return localDate(new Date())
}

export function yearAgoStr(): string {
  const d = new Date()
  d.setFullYear(d.getFullYear() - 1)
  return localDate(d)
}

export function monthsAgoStr(n: number): string {
  const d = new Date()
  d.setMonth(d.getMonth() - n)
  return localDate(d)
}

export function defaultDateRange(): { start_date: string; end_date: string } {
  return { start_date: yearAgoStr(), end_date: todayStr() }
}

export function isTradingTime(d = new Date()): boolean {
  const day = d.getDay()
  if (day === 0 || day === 6) return false
  const mins = d.getHours() * 60 + d.getMinutes()
  return (mins >= 570 && mins < 690) || (mins >= 780 && mins < 900)
}
