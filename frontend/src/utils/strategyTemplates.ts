export interface StrategyTemplate {
  key: string
  name: string
  description: string
  config: {
    buy: Record<string, Record<string, unknown>>
    sell: Record<string, Record<string, unknown>>
    risk: Record<string, number>
  }
}

export const STRATEGY_TEMPLATES: StrategyTemplate[] = [
  {
    key: 'maTrend',
    name: '均线趋势',
    description: '5/20 均线金叉买入，死叉卖出，配合止盈止损与移动止盈',
    config: {
      buy: {
        maCross: { enabled: true, shortPeriod: 5, longPeriod: 20 },
      },
      sell: {
        maDeathCross: { enabled: true, shortPeriod: 5, longPeriod: 20 },
        takeProfit: { enabled: true, percent: 15 },
        stopLoss: { enabled: true, percent: 8 },
        trailingStop: { enabled: true, drawdown: 10 },
      },
      risk: {
        maxPositionPercent: 20,
        maxHoldings: 10,
        maxSingleLoss: 15,
        totalStopLoss: 20,
        maxDrawdown: 25,
      },
    },
  },
  {
    key: 'breakoutMomentum',
    name: '突破动量',
    description: '突破 20 日新高且放量买入，移动止盈与持有天数到期卖出',
    config: {
      buy: {
        breakHigh: { enabled: true, days: 20 },
        volumeBreak: { enabled: true, multiple: 1.5, avgDays: 5 },
      },
      sell: {
        trailingStop: { enabled: true, drawdown: 8 },
        maxHoldDays: { enabled: true, days: 20 },
      },
      risk: {
        maxPositionPercent: 25,
        maxHoldings: 8,
        maxSingleLoss: 15,
        totalStopLoss: 20,
        maxDrawdown: 25,
      },
    },
  },
  {
    key: 'oversoldRebound',
    name: '超跌反弹',
    description: 'RSI 超卖 + 布林下轨反弹买入，RSI 超买或固定止盈止损卖出',
    config: {
      buy: {
        rsiOversold: { enabled: true, period: 14, threshold: 30 },
        bollLowerRebound: { enabled: true, period: 20, numStd: 2 },
      },
      sell: {
        takeProfit: { enabled: true, percent: 8 },
        stopLoss: { enabled: true, percent: 5 },
        rsiOverbought: { enabled: true, period: 14, threshold: 65 },
      },
      risk: {
        maxPositionPercent: 15,
        maxHoldings: 12,
        maxSingleLoss: 10,
        totalStopLoss: 15,
        maxDrawdown: 20,
      },
    },
  },
  {
    key: 'steadyValue',
    name: '稳健价值',
    description: 'KDJ 低位金叉 + 布林下轨买入，KDJ 高位死叉或跌破中轨卖出，风控严格',
    config: {
      buy: {
        kdjGoldenCross: { enabled: true, n: 9, lowZone: 50 },
        bollLowerRebound: { enabled: true, period: 20, numStd: 2 },
      },
      sell: {
        kdjDeathCross: { enabled: true, n: 9, highZone: 50 },
        bollBelowMid: { enabled: true, period: 20, numStd: 2 },
        stopLoss: { enabled: true, percent: 5 },
      },
      risk: {
        maxPositionPercent: 15,
        maxHoldings: 10,
        maxSingleLoss: 10,
        totalStopLoss: 15,
        maxDrawdown: 20,
      },
    },
  },
  {
    key: 'shortTerm',
    name: '短线快进快出',
    description: '5/10 均线金叉 + 放量突破买入，快速止盈止损，最大持有 5 天',
    config: {
      buy: {
        maCross: { enabled: true, shortPeriod: 5, longPeriod: 10 },
        volumeBreak: { enabled: true, multiple: 1.5, avgDays: 5 },
      },
      sell: {
        takeProfit: { enabled: true, percent: 5 },
        stopLoss: { enabled: true, percent: 3 },
        maxHoldDays: { enabled: true, days: 5 },
      },
      risk: {
        maxPositionPercent: 10,
        maxHoldings: 8,
        maxSingleLoss: 5,
        totalStopLoss: 10,
        maxDrawdown: 15,
      },
    },
  },
  {
    key: 'swing',
    name: '波段趋势',
    description: '20/60 均线金叉买入，移动止盈与均线死叉卖出，适合波段持股',
    config: {
      buy: {
        maCross: { enabled: true, shortPeriod: 20, longPeriod: 60 },
      },
      sell: {
        maDeathCross: { enabled: true, shortPeriod: 20, longPeriod: 60 },
        trailingStop: { enabled: true, drawdown: 12 },
        stopLoss: { enabled: true, percent: 8 },
      },
      risk: {
        maxPositionPercent: 20,
        maxHoldings: 6,
        maxSingleLoss: 12,
        totalStopLoss: 18,
        maxDrawdown: 20,
      },
    },
  },
]
