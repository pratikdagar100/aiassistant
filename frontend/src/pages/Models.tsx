import { useEffect, useState } from 'react'

interface ModelInfo {
  name: string
  installed: boolean
  size_bytes: number | null
  parameter_size: string | null
  quantization: string | null
  is_default: boolean
}

function formatBytes(bytes: number | null): string {
  if (!bytes) return '—'
  const gb = bytes / (1024 * 1024 * 1024)
  return `${gb.toFixed(1)} GB`
}

export function Models() {
  const [models, setModels] = useState<ModelInfo[]>([])
  const [error, setError] = useState<string | null>(null)
  const [pulling, setPulling] = useState<string | null>(null)
  const [progress, setProgress] = useState<string>('')

  async function load() {
    try {
      const res = await fetch('/api/models')
      if (!res.ok) throw new Error(`${res.status}`)
      setModels(await res.json())
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    }
  }

  useEffect(() => {
    load()
    const interval = setInterval(load, 8000)
    return () => clearInterval(interval)
  }, [])

  async function pull(name: string) {
    setPulling(name)
    setProgress('starting…')
    const res = await fetch('/api/models/pull', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    })
    if (!res.body) return
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''
      for (const line of lines) {
        if (!line.trim()) continue
        const event = JSON.parse(line)
        if (event.status) setProgress(event.status + (event.completed && event.total ? ` ${Math.round((event.completed / event.total) * 100)}%` : ''))
        if (event.error) setProgress(`error: ${event.error}`)
      }
    }
    setPulling(null)
    load()
  }

  return (
    <div className="flex-1 overflow-y-auto p-8">
      <h1 className="mb-1 text-2xl font-semibold text-zinc-100">Models</h1>
      <p className="mb-6 text-sm text-zinc-500">
        Local models available through Ollama. RTX 3060 has 12GB VRAM — check size before installing more than one
        large model.
      </p>

      {error && (
        <div className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
          Could not load models: {error}
        </div>
      )}

      <div className="overflow-hidden rounded-lg border border-zinc-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-zinc-900 text-zinc-400">
            <tr>
              <th className="px-4 py-2 font-medium">Model</th>
              <th className="px-4 py-2 font-medium">Status</th>
              <th className="px-4 py-2 font-medium">Size</th>
              <th className="px-4 py-2 font-medium">Params</th>
              <th className="px-4 py-2 font-medium">Quant</th>
              <th className="px-4 py-2 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {models.map((m) => (
              <tr key={m.name} className="border-t border-zinc-800 text-zinc-200">
                <td className="px-4 py-2 font-mono text-xs">
                  {m.name}
                  {m.is_default && (
                    <span className="ml-2 rounded bg-violet-600/20 px-1.5 py-0.5 text-[10px] text-violet-300">
                      default
                    </span>
                  )}
                </td>
                <td className="px-4 py-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs ${
                      m.installed ? 'bg-emerald-500/15 text-emerald-400' : 'bg-zinc-700/40 text-zinc-400'
                    }`}
                  >
                    {m.installed ? 'installed' : 'not installed'}
                  </span>
                </td>
                <td className="px-4 py-2 text-zinc-400">{formatBytes(m.size_bytes)}</td>
                <td className="px-4 py-2 text-zinc-400">{m.parameter_size ?? '—'}</td>
                <td className="px-4 py-2 text-zinc-400">{m.quantization ?? '—'}</td>
                <td className="px-4 py-2">
                  {!m.installed && (
                    <button
                      onClick={() => pull(m.name)}
                      disabled={pulling !== null}
                      className="rounded bg-violet-600 px-3 py-1 text-xs font-medium text-white disabled:opacity-40"
                    >
                      {pulling === m.name ? progress || 'pulling…' : 'Install'}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
