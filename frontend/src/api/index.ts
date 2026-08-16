import { http, streamNDJSON, type StreamEvent } from './http'
import type {
  Account,
  BacktestResult,
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

export const accountApi = {
  get: () => http.get<Account>('/account'),
  reset: () => http.post<{ ok: boolean }>('/account/reset'),
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
  list: (sid: number) =>
    http.get<Omit<BacktestResult, 'equity_curve' | 'trades' | 'signal_stats'>[]>(
      `/strategies/${sid}/backtests`,
    ),
  get: (sid: number, bid: number) => http.get<BacktestResult>(`/strategies/${sid}/backtests/${bid}`),
}

export const generatorApi = {
  run: (req: GenerationRequest) => http.post<Record<string, unknown>>('/generator/run', req),
  stream: (req: GenerationRequest, onEvent: (e: StreamEvent) => void) =>
    streamNDJSON('/generator/run/stream', req, onEvent),
  reports: () => http.get<Record<string, unknown>[]>('/generator/reports'),
  report: (gid: number) => http.get<Record<string, unknown>>(`/generator/reports/${gid}`),
}

export const stockApi = {
  list: () => http.get<Stock[]>('/stocks'),
  bars: (code: string, days = 90) => http.get<Bar[]>(`/stocks/${code}/bars?days=${days}`),
}

export const orderApi = {
  prepare: (input: OrderPrepareInput) =>
    http.post<{ request_id: string; status: string; order: OrderPrepareInput }>('/orders/prepare', input),
  confirm: (requestId: string) =>
    http.post<{ status: string; reason: string; order_id: number }>(`/orders/confirm/${requestId}`),
}
