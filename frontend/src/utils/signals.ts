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

export const PARAM_LABELS: Record<string, string> = {
  shortPeriod: '短周期',
  longPeriod: '长周期',
  fast: '快线',
  slow: '慢线',
  signal: '信号线',
  days: '天数',
  multiple: '倍数',
  avgDays: '均量天数',
  period: '周期',
  threshold: '阈值',
  n: 'N周期',
  lowZone: '低位区',
  highZone: '高位区',
  numStd: '标准差倍数',
  percent: '百分比%',
  drawdown: '回撤%',
}

export const RISK_LABELS: Record<string, string> = {
  maxPositionPercent: '单只最大仓位%',
  maxHoldings: '最大持仓数',
  maxSingleLoss: '单只最大亏损%',
  totalStopLoss: '组合整体止损%',
  maxDrawdown: '最大回撤%',
}

export function signalParamText(cfg: Record<string, unknown>): string {
  const parts = Object.keys(cfg)
    .filter((k) => k !== 'enabled')
    .map((k) => `${PARAM_LABELS[k] ?? k} ${cfg[k]}`)
  return parts.join(' · ')
}
