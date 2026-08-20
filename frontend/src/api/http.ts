import { toast } from '../utils/toast'
import { markOffline, markOnline } from '../composables/netStatus'

const BASE = '/api'
const MAX_RETRIES = 2

let lastNetworkToastAt = 0
let lastErrToastAt = 0
let lastErrToastKey = ''

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms))
}

function throttledNetworkToast() {
  const now = Date.now()
  if (now - lastNetworkToastAt < 3000) return
  lastNetworkToastAt = now
  toast('网络连接失败，正在重试')
}

function throttledErrorToast(detail: string) {
  const now = Date.now()
  const msg = detail && detail.length <= 40 ? detail : '数据加载失败，请稍后重试'
  if (now - lastErrToastAt < 3000 && lastErrToastKey === msg) return
  lastErrToastAt = now
  lastErrToastKey = msg
  toast(msg)
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json()
    return data.detail || JSON.stringify(data)
  } catch {
    return await res.text().catch(() => '')
  }
}

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let res: Response | null = null
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      res = await fetch(`${BASE}${path}`, {
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders(), ...(options.headers || {}) },
        ...options,
      })
      markOnline()
      break
    } catch {
      markOffline()
      if (attempt < MAX_RETRIES) {
        await sleep(600 * 2 ** attempt)
      }
    }
  }
  if (!res) {
    throttledNetworkToast()
    throw new Error('网络连接失败')
  }
  if (!res.ok) {
    const detail = await parseError(res)
    throttledErrorToast(detail)
    throw new Error(detail || `请求失败 (${res.status})`)
  }
  return res.json() as Promise<T>
}

export const http = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body !== undefined ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  del: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}

export type StreamEvent = Record<string, unknown>

export async function streamNDJSON(
  path: string,
  body: unknown,
  onEvent: (evt: StreamEvent) => void,
): Promise<void> {
  let res: Response | null = null
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      res = await fetch(`${BASE}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      markOnline()
      break
    } catch {
      markOffline()
      if (attempt < MAX_RETRIES) {
        await sleep(600 * 2 ** attempt)
      }
    }
  }
  if (!res) {
    throttledNetworkToast()
    throw new Error('网络连接失败')
  }
  if (!res.ok || !res.body) {
    const detail = await parseError(res)
    throttledErrorToast(detail)
    throw new Error(detail || `请求失败 (${res.status})`)
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let idx = buffer.indexOf('\n')
    while (idx >= 0) {
      const line = buffer.slice(0, idx).trim()
      buffer = buffer.slice(idx + 1)
      if (line) {
        try {
          onEvent(JSON.parse(line))
        } catch {
          // 忽略无法解析的行
        }
      }
      idx = buffer.indexOf('\n')
    }
  }
}
