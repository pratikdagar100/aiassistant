import { useEffect, useState } from 'react'

interface MemoryItem {
  id: number
  entity_id: string
  memory_type: string
  category: string
  content: string
  importance: number
  confidence: number
  source: string | null
  pinned: boolean
  created_at: string
}

export function Memory() {
  const [memories, setMemories] = useState<MemoryItem[]>([])
  const [search, setSearch] = useState('')
  const [error, setError] = useState<string | null>(null)
  const entityId = 'friday' // Phase 4 scope: single-entity view; entity switcher lands with the rest of multi-entity UI polish

  async function load() {
    try {
      const params = new URLSearchParams({ entity_id: entityId })
      if (search) params.set('search', search)
      const res = await fetch(`/api/memory?${params}`)
      if (!res.ok) throw new Error(`${res.status}`)
      setMemories(await res.json())
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search])

  async function togglePin(m: MemoryItem) {
    await fetch(`/api/memory/${m.id}/pin?pinned=${!m.pinned}`, { method: 'POST' })
    load()
  }

  async function remove(m: MemoryItem) {
    if (!confirm('Delete this memory?')) return
    await fetch(`/api/memory/${m.id}`, { method: 'DELETE' })
    load()
  }

  async function clearAll() {
    if (!confirm(`Delete ALL memories for ${entityId}? This cannot be undone.`)) return
    await fetch(`/api/memory?entity_id=${entityId}`, { method: 'DELETE' })
    load()
  }

  return (
    <div className="flex-1 overflow-y-auto p-8">
      <div className="mb-1 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-100">Memory — {entityId}</h1>
        <button onClick={clearAll} className="text-xs text-red-400 hover:text-red-300">
          Clear all
        </button>
      </div>
      <p className="mb-4 text-sm text-zinc-500">
        Extracted automatically from conversation, or added manually. Pinned memories are always included in context.
      </p>

      <input
        className="input mb-6"
        placeholder="Search memories…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      {error && (
        <div className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">{error}</div>
      )}

      <div className="space-y-2">
        {memories.length === 0 && <div className="text-sm text-zinc-600">No memories yet.</div>}
        {memories.map((m) => (
          <div key={m.id} className="flex items-start justify-between gap-4 rounded-lg border border-zinc-800 bg-zinc-900 p-4">
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-1.5 text-[10px] text-zinc-500">
                <span className="rounded border border-zinc-700 px-1.5 py-0.5">{m.category}</span>
                <span className="rounded border border-zinc-700 px-1.5 py-0.5">{m.memory_type}</span>
                <span>importance {m.importance.toFixed(2)}</span>
                {m.source && <span>· {m.source}</span>}
              </div>
              <p className="mt-1.5 text-sm text-zinc-200">{m.content}</p>
            </div>
            <div className="flex shrink-0 gap-2">
              <button
                onClick={() => togglePin(m)}
                className={`text-xs ${m.pinned ? 'text-amber-400' : 'text-zinc-500 hover:text-zinc-300'}`}
              >
                {m.pinned ? '★ pinned' : '☆ pin'}
              </button>
              <button onClick={() => remove(m)} className="text-xs text-red-400 hover:text-red-300">
                delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
