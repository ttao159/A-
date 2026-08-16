import { http, streamNDJSON, type StreamEvent } from './http'
import type {
  Account,
  BacktestListItem,
  BacktestResult,
  GenerationReport,
  GenerationReportItem,
  GenerationRequest,
  Order,
  OrderPrepareInput,
  Position,
  ScanReports,
  ScanResult,
  Strategy,
  StrategyInput,
  Trade,
} from './types'

export interface Bar {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface Stock {
  code: string
  name: string
}

export interface MinuteBar {
  time: string
  price: number
  volume: number
}

export interface MinuteData {
  prev_close: number
  bars: MinuteBar[]
}

export const accountApi = {
  get: () => http.get<Account>('/account'),
  equity: () => http.get<AccountEquityPoint[]>('/account/equity'),
  dailyPnl: () => http.get<DailyPnlPoint[]>('/account/daily-pnl'),
  reset: () => http.post<{ ok: boolean }>('/account/reset'),
}

export interface AccountEquityPoint {
  date: string
  equity: number
}

export interface DailyPnlPoint {
  date: string
  equity: number
  pnl: number
}

export interface IndexQuote {
  code: string
  name: string
  price: number
  change: number
  change_pct: number
}

export const indexApi = {
  list: () => http.get<IndexQuote[]>('/indices'),
}

export const strategyApi = {
  list: () => http.get<Strategy[]>('/strategies'),
  create: (input: StrategyInput) => http.post<Strategy>('/strategies', input),
  update: (id: number, input: StrategyInput) => http.put<Strategy>(`/strategies/${id}`, input),
  remove: (id: number) => http.del<{ ok: boolean }>(`/strategies/${id}`),
}

export const positionApi = {
  list: () => http.get<Position[]>('/positions'),
}

export const tradeApi = {
  list: () => http.get<Trade[]>('/trades'),
  orders: () => http.get<Order[]>('/orders'),
}

export const scanApi = {
  run: () => http.post<ScanResult>('/scan'),
  stream: (onEvent: (e: StreamEvent) => void) => streamNDJSON('/scan/stream', {}, onEvent),
  reports: () => http.get<ScanReports>('/scan/reports'),
}

export const backtestApi = {
  run: (sid: number, start: string, end: string) =>
    http.post<BacktestResult>(`/strategies/${sid}/backtest`, { start_date: start, end_date: end }),
  list: (sid: number) => http.get<BacktestListItem[]>(`/strategies/${sid}/backtests`),
  get: (sid: number, bid: number) => http.get<BacktestResult>(`/strategies/${sid}/backtests/${bid}`),
}

export const generatorApi = {
  run: (req: GenerationRequest) => http.post<GenerationReport>('/generator/run', req),
  stream: (req: GenerationRequest, onEvent: (e: StreamEvent) => void) =>
    streamNDJSON('/generator/run/stream', req, onEvent),
  reports: () => http.get<GenerationReportItem[]>('/generator/reports'),
  report: (gid: number) => http.get<GenerationReport>(`/generator/reports/${gid}`),
}

export const stockApi = {
  list: () => http.get<Stock[]>('/stocks'),
  bars: (code: string, days = 90, period = 'day') =>
    http.get<Bar[]>(`/stocks/${code}/bars?days=${days}&period=${period}`),
  minute: (code: string) => http.get<MinuteData>(`/stocks/${code}/minute`),
}

export const orderApi = {
  prepare: (input: OrderPrepareInput) =>
    http.post<{ request_id: string; status: string; order: OrderPrepareInput }>('/orders/prepare', input),
  confirm: (requestId: string) =>
    http.post<{ status: string; reason: string; order_id: number }>(`/orders/confirm/${requestId}`),
}

export interface Alert {
  id: number
  code: string
  name: string
  type: string
  message: string
  price: number
  created_at: string | null
}

export const alertApi = {
  list: () => http.get<Alert[]>('/alerts'),
}
