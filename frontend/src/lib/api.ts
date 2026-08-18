export interface HealthCheck {
  status: 'READY' | 'WARNING' | 'ERROR'
  detail?: string
  [key: string]: unknown
}

export interface HealthResponse {
  status: 'READY' | 'WARNING' | 'ERROR'
  app_name: string
  version: string
  phase: number
  timestamp: number
  checks: Record<string, HealthCheck>
}

// Vite dev server proxies /api -> the FastAPI backend (see vite.config.ts).
const API_BASE = '/api'

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) {
    throw new Error(`Health check request failed: ${res.status}`)
  }
  return res.json()
}
