export interface StrategyConfig {
  buy: Record<string, Record<string, unknown>>
  sell: Record<string, Record<string, unknown>>
  risk: Record<string, number>
}

export interface Strategy {
  id: number
  name: string
  enabled: boolean
  config: StrategyConfig
  initial_capital: number
  available_cash: number
  created_at: string | null
  updated_at: string | null
}

export interface StrategyInput {
  name?: string
  enabled?: boolean
  config?: StrategyConfig
  initial_capital?: number
}

export interface StrategyCompareItem {
  id: number
  name: string
  enabled: boolean
  initial_capital: number
  available_cash: number
  market_value: number
  total_asset: number
  pnl: number
  return_pct: number
}

export interface Account {
  broker_type: string
  initial_capital: number
  available_cash: number
  market_value: number
  total_asset: number
  total_pnl: number
  today_pnl: number
}

export interface Position {
  code: string
  name: string
  qty: number
  avg_cost: number
  price: number
  pnl_pct: number
  pnl: number
  hold_days: number
  strategy_id: number | null
  strategy_name: string | null
}

export interface Trade {
  id: number
  code: string
  name: string
  direction: string
  qty: number
  price: number
  commission: number
  tax: number
  pnl: number
  traded_at: string | null
}

export interface Order {
  id: number
  code: string
  name: string
  direction: string
  qty: number
  price: number
  status: string
  reason: string
  broker_type: string
  external_order_id: string | null
  created_at: string | null
}

export interface BacktestMetrics {
  initial_capital?: number
  final_equity?: number
  total_return_pct?: number
  annual_return_pct?: number
  max_drawdown_pct?: number
  max_drawdown_days?: number
  annual_volatility_pct?: number
  sharpe_ratio?: number
  sortino_ratio?: number
  calmar_ratio?: number
  win_rate_pct?: number
  profit_loss_ratio?: number
  trade_count?: number
  closed_trades?: number
}

export interface EquityPoint {
  date: string
  equity: number
}

export interface BacktestResult {
  id: number
  strategy_id: number
  start_date: string
  end_date: string
  metrics: BacktestMetrics
  equity_curve: EquityPoint[]
  trades: Record<string, unknown>[]
  signal_stats?: Record<string, unknown>
}

export interface BacktestListItem {
  id: number
  strategy_id: number
  start_date: string
  end_date: string
  metrics: BacktestMetrics
  created_at: string | null
}

export interface OptimizeResultItem {
  params: Record<string, unknown>
  metrics: BacktestMetrics
}

export interface ScanStats {
  total_scans: number
  total_buys: number
  total_sells: number
  total_rejects: number
}

export interface ScanReportItem {
  id: number
  strategy_count: number
  buy_count: number
  sell_count: number
  reject_count: number
  source: string
  created_at: string | null
}

export interface ScanReports {
  scan_schedule?: { hour: number; minute: number; broker_type: string }
  stats: ScanStats
  items: ScanReportItem[]
}

export interface ScanResult {
  buys: Record<string, unknown>[]
  sells: Record<string, unknown>[]
  rejected: Record<string, unknown>[]
  strategy_count: number
}

export interface GenerationRequest {
  targets: { scope: string; codes: string[] }
  start_date: string
  end_date: string
  risk_profile: string
  count: number
  target_annual_return?: number
  analysis_depth?: string
}

export interface GenDecision {
  rating: string
  risk_level: string
  action: string
  confidence: number
  summary: string
}

export interface AgentAnalysis {
  available: boolean
  fallback?: string
  verdict?: string
  opinions?: Record<string, string>
  bull_case?: string
  bear_case?: string
  target_price?: number
  stop_loss?: number
  position_suggestion?: string
  action?: string
  confidence?: number
}

export interface GenStrategy {
  index: number
  signals: { buy: string[]; sell: string[] }
  config: Record<string, unknown>
  metrics: BacktestMetrics
  decision: GenDecision
  equity_curve: EquityPoint[]
  trades: Record<string, unknown>[]
}

export interface GenerationReport {
  id?: number
  request: Record<string, unknown>
  strategies: GenStrategy[]
  ranking: { index: number; score: number }[]
  recommended_index: number
  agent_analysis?: AgentAnalysis
}

export interface GenerationReportItem {
  id: number
  created_at: string | null
  recommended_index: number
  request: Record<string, unknown>
}

export interface OrderPrepareInput {
  code: string
  name?: string
  direction: string
  price: number
  qty: number
  strategy_id?: number | null
  reason?: string
}
