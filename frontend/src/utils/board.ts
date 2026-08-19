export function isMainBoard(code: string): boolean {
  return /^\d{6}$/.test(code) && (code.startsWith('60') || code.startsWith('00'))
}

export function isBlockedBoard(code: string): boolean {
  if (!/^\d{6}$/.test(code)) return false
  return code.startsWith('300') || code.startsWith('301') || code.startsWith('688') || code.startsWith('689')
}
