export const ALERT_LABELS: Record<string, string> = {
  takeProfit: '止盈',
  stopLoss: '止损',
  trailingStop: '移动止盈',
  maxSingleLoss: '最大亏损',
  strategy_failed: '策略失效',
}

export function alertTypeLabel(type: string) {
  return ALERT_LABELS[type] ?? type
}

export function isProfitAlert(type: string) {
  return type === 'takeProfit' || type === 'trailingStop'
}
