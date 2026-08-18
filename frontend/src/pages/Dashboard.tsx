import { useEffect, useState } from 'react'
import { fetchHealth, type HealthResponse } from '../lib/api'
import { StatusBadge } from '../components/StatusBadge'

export function Dashboard() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const data = await fetchHealth()
        if (!cancelled) {
          setHealth(data)
          setError(null)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Unknown error')
          setHealth(null)
        }
      }
    }

    load()
    const interval = setInterval(load, 5000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [])

  return (
    <div className="flex-1 overflow-y-auto p-8">
      <h1 className="mb-1 text-2xl font-semibold text-zinc-100">Dashboard</h1>
      <p className="mb-6 text-sm text-zinc-500">
        Phase 1 — foundation. This page reflects the live status of the backend, database, and
        Ollama connection; nothing here is simulated.
      </p>

      {error && (
        <div className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
          Could not reach the backend at /api/health: {error}
          <br />
          Start it with <code className="rounded bg-black/30 px-1">scripts\start.ps1</code>.
        </div>
      )}

      {health && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-zinc-400">Overall</span>
              <StatusBadge status={health.status} />
            </div>
            <div className="mt-2 text-xs text-zinc-600">
              {health.app_name} v{health.version} — Phase {health.phase}
            </div>
          </div>

          {Object.entries(health.checks).map(([name, check]) => (
            <div key={name} className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm capitalize text-zinc-400">{name}</span>
                <StatusBadge status={check.status} />
              </div>
              {check.detail ? (
                <div className="mt-2 text-xs text-zinc-600">{String(check.detail)}</div>
              ) : (
                Object.entries(check)
                  .filter(([k]) => k !== 'status')
                  .map(([k, v]) => (
                    <div key={k} className="mt-1 text-xs text-zinc-600">
                      {k}: {String(v)}
                    </div>
                  ))
              )}
            </div>
          ))}
        </div>
      )}

      {!health && !error && <div className="text-sm text-zinc-500">Loading…</div>}
    </div>
  )
}
