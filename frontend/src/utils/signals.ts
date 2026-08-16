export const BUY_LABELS: Record<string, string> = {
  maCross: '均线金叉',
  macdCross: 'MACD金叉',
  breakHigh: '突破新高',
  volumeBreak: '放量突破',
  hammer: '锤子线',
  bullishEngulfing: '看涨吞没',
  morningStar: '早晨之星',
  threeWhiteSoldiers: '红三兵',
  doubleBottom: '双底',
  rsiOversold: 'RSI超卖',
  kdjGoldenCross: 'KDJ低位金叉',
  bollLowerRebound: '布林下轨反弹',
}

export const SELL_LABELS: Record<string, string> = {
  takeProfit: '固定止盈',
  stopLoss: '固定止损',
  trailingStop: '移动止盈',
  maDeathCross: '均线死叉',
  macdDeathCross: 'MACD死叉',
  belowMA: '跌破均线',
  maxHoldDays: '持有天数到期',
  hangingMan: '上吊线',
  bearishEngulfing: '看跌吞没',
  eveningStar: '黄昏之星',
  threeBlackCrows: '三只乌鸦',
  doubleTop: '双顶',
  rsiOverbought: 'RSI超买',
  kdjDeathCross: 'KDJ高位死叉',
  bollBelowMid: '跌破布林中轨',
}

export function signalName(key: string): string {
  return BUY_LABELS[key] ?? SELL_LABELS[key] ?? key
}

export function sigNames(signals: { buy?: string[]; sell?: string[] }): string {
  const buy = (signals.buy ?? []).map(signalName)
  const sell = (signals.sell ?? []).map(signalName)
  return [...buy, ...sell].join(' / ') || '—'
}
