import { useEffect, useState } from 'react'
import { listEntities, type EntitySummary } from '../lib/entities'

interface Tool {
  tool: string
  category: string
  risk: string
  description: string
}

interface PendingApproval {
  id: number
  tool: string
  parameters: Record<string, unknown>
  risk_level: string
  timestamp: string
}

export function Computer() {
  const [entities, setEntities] = useState<EntitySummary[]>([])
  const [entityId, setEntityId] = useState('friday')
  const [tools, setTools] = useState<Tool[]>([])
  const [selectedTool, setSelectedTool] = useState('')
  const [paramsText, setParamsText] = useState('{}')
  const [result, setResult] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState<PendingApproval[]>([])

  useEffect(() => {
    listEntities().then(setEntities).catch(() => setEntities([]))
    fetch('/api/computer/tools')
      .then((r) => r.json())
      .then((ts: Tool[]) => {
        setTools(ts)
        if (ts.length) setSelectedTool(ts[0].tool)
      })
  }, [])

  async function loadPending() {
    const res = await fetch(`/api/audit?entity_id=${entityId}`)
    if (!res.ok) return
    const all = await res.json()
    setPending(all.filter((a: { approval_required: boolean; approved: boolean | null }) => a.approval_required && a.approved === null))
  }

  useEffect(() => {
    loadPending()
    const interval = setInterval(loadPending, 4000)
    return () => clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entityId])

  async function execute() {
    setError(null)
    setResult(null)
    let parameters: Record<string, unknown>
    try {
      parameters = JSON.parse(paramsText)
    } catch {
      setError('Parameters must be valid JSON')
      return
    }

    const res = await fetch('/api/computer/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entity_id: entityId, tool: selectedTool, parameters }),
    })
    const body = await res.json()
    if (!res.ok) {
      setError(body.detail ?? `Error ${res.status}`)
      return
    }
    if (body.status === 'pending_approval') {
      setResult('Pending approval — see below.')
      loadPending()
    } else {
      setResult(JSON.stringify(body.result, null, 2))
    }
  }

  async function respond(auditId: number, action: 'approve' | 'deny') {
    await fetch(`/api/computer/${action}/${auditId}`, { method: 'POST' })
    loadPending()
  }

  const activeTool = tools.find((t) => t.tool === selectedTool)

  return (
    <div className="flex-1 overflow-y-auto p-8">
      <div className="mb-1 flex items-center gap-3">
        <h1 className="text-2xl font-semibold text-zinc-100">Computer Control</h1>
        <select value={entityId} onChange={(e) => setEntityId(e.target.value)} className="rounded border border-zinc-800 bg-zinc-900 px-2 py-1 text-sm text-zinc-200">
          {entities.length === 0 && <option value="friday">friday</option>}
          {entities.map((e) => (
            <option key={e.id} value={e.id}>
              {e.name}
            </option>
          ))}
        </select>
      </div>
      <p className="mb-6 text-sm text-zinc-500">
        Every call goes through the permission system — disabled categories are rejected, confirmation categories
        wait for approval below before anything runs.
      </p>

      <div className="mb-6 rounded-lg border border-zinc-800 bg-zinc-900 p-4">
        <div className="mb-3 flex gap-2">
          <select
            value={selectedTool}
            onChange={(e) => setSelectedTool(e.target.value)}
            className="flex-1 rounded border border-zinc-800 bg-zinc-950 px-2 py-1.5 text-sm text-zinc-200"
          >
            {tools.map((t) => (
              <option key={t.tool} value={t.tool}>
                {t.tool} ({t.risk})
              </option>
            ))}
          </select>
          <button onClick={execute} className="rounded bg-violet-600 px-4 py-1.5 text-sm font-medium text-white">
            Execute
          </button>
        </div>
        {activeTool && <p className="mb-2 text-xs text-zinc-500">{activeTool.description} · category: {activeTool.category}</p>}
        <textarea
          value={paramsText}
          onChange={(e) => setParamsText(e.target.value)}
          rows={3}
          className="input font-mono text-xs"
          placeholder='{"path": "C:\\Users\\..."}'
        />
        {error && <div className="mt-3 rounded bg-red-500/10 p-2 text-xs text-red-400">{error}</div>}
        {result && <pre className="mt-3 max-h-40 overflow-auto rounded bg-black/30 p-2 text-xs text-zinc-300">{result}</pre>}
      </div>

      <h2 className="mb-2 text-sm font-medium text-zinc-300">Pending approvals</h2>
      <div className="space-y-2">
        {pending.length === 0 && <div className="text-sm text-zinc-600">Nothing pending.</div>}
        {pending.map((p) => (
          <div key={p.id} className="flex items-center justify-between rounded-lg border border-amber-500/30 bg-amber-500/5 p-3">
            <div className="text-sm">
              <span className="font-mono text-zinc-200">{p.tool}</span>
              <span className="ml-2 rounded bg-amber-500/20 px-1.5 py-0.5 text-[10px] text-amber-400">{p.risk_level}</span>
              <div className="mt-1 text-xs text-zinc-500">{JSON.stringify(p.parameters)}</div>
            </div>
            <div className="flex gap-2">
              <button onClick={() => respond(p.id, 'approve')} className="rounded bg-emerald-600 px-3 py-1 text-xs font-medium text-white">
                Approve
              </button>
              <button onClick={() => respond(p.id, 'deny')} className="rounded bg-red-600 px-3 py-1 text-xs font-medium text-white">
                Deny
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
