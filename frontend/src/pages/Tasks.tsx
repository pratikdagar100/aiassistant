import { useEffect, useState } from 'react'
import { listEntities, type EntitySummary } from '../lib/entities'

interface TaskStep {
  id: number
  step_index: number
  description: string
  tool: string | null
  status: string
  result: string | null
}

interface TaskItem {
  id: number
  entity_id: string
  description: string
  status: string
  created_at: string
  steps: TaskStep[]
}

const STEP_ICON: Record<string, string> = {
  pending: '○',
  running: '→',
  success: '✓',
  failed: '✗',
  pending_approval: '⏸',
  skipped: '–',
}

export function Tasks() {
  const [entities, setEntities] = useState<EntitySummary[]>([])
  const [entityId, setEntityId] = useState('friday')
  const [tasks, setTasks] = useState<TaskItem[]>([])
  const [description, setDescription] = useState('')
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    listEntities().then(setEntities).catch(() => setEntities([]))
  }, [])

  async function load() {
    const res = await fetch(`/api/tasks?entity_id=${entityId}`)
    if (res.ok) setTasks(await res.json())
  }

  useEffect(() => {
    load()
    const interval = setInterval(load, 4000)
    return () => clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entityId])

  async function create() {
    if (!description.trim()) return
    setCreating(true)
    setError(null)
    const res = await fetch('/api/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entity_id: entityId, description }),
    })
    const body = await res.json()
    setCreating(false)
    if (!res.ok) {
      setError(body.detail ?? `Error ${res.status}`)
      return
    }
    setDescription('')
    load()
  }

  async function act(taskId: number, action: 'resume' | 'replan' | 'cancel') {
    await fetch(`/api/tasks/${taskId}/${action}`, { method: 'POST' })
    load()
  }

  const activeEntity = entities.find((e) => e.id === entityId)
  const autonomyOk = (activeEntity?.autonomy_level ?? 0) >= 6

  return (
    <div className="flex-1 overflow-y-auto p-8">
      <div className="mb-1 flex items-center gap-3">
        <h1 className="text-2xl font-semibold text-zinc-100">Tasks</h1>
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
        Autonomous multi-step tasks: plan → execute → observe → verify → replan. Requires autonomy level ≥ 6
        {activeEntity && !autonomyOk && <> — {activeEntity.name} is currently at {activeEntity.autonomy_level}.</>}
      </p>

      <div className="mb-6 flex gap-2">
        <input
          className="input flex-1"
          placeholder="Describe a task, e.g. 'Find the largest file in Downloads'"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && create()}
        />
        <button onClick={create} disabled={creating || !description.trim()} className="rounded bg-violet-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-40">
          {creating ? 'Planning…' : 'Start Task'}
        </button>
      </div>
      {error && <div className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">{error}</div>}

      <div className="space-y-4">
        {tasks.map((t) => (
          <div key={t.id} className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
            <div className="mb-2 flex items-center justify-between">
              <div className="text-sm text-zinc-200">{t.description}</div>
              <div className="flex items-center gap-2">
                <span
                  className={`rounded-full px-2 py-0.5 text-xs ${
                    t.status === 'completed'
                      ? 'bg-emerald-500/15 text-emerald-400'
                      : t.status === 'failed'
                        ? 'bg-red-500/15 text-red-400'
                        : t.status === 'paused'
                          ? 'bg-amber-500/15 text-amber-400'
                          : 'bg-zinc-700/40 text-zinc-400'
                  }`}
                >
                  {t.status}
                </span>
                {t.status === 'paused' && (
                  <button onClick={() => act(t.id, 'resume')} className="rounded bg-emerald-600 px-2 py-1 text-xs text-white">
                    Resume
                  </button>
                )}
                {t.status === 'failed' && (
                  <button onClick={() => act(t.id, 'replan')} className="rounded bg-violet-600 px-2 py-1 text-xs text-white">
                    Replan
                  </button>
                )}
                {(t.status === 'running' || t.status === 'paused' || t.status === 'planning') && (
                  <button onClick={() => act(t.id, 'cancel')} className="rounded bg-zinc-700 px-2 py-1 text-xs text-white">
                    Cancel
                  </button>
                )}
              </div>
            </div>
            <div className="space-y-1">
              {t.steps.map((s) => (
                <div key={s.id} className="flex items-start gap-2 text-xs">
                  <span className="w-4 text-zinc-500">{STEP_ICON[s.status] ?? '?'}</span>
                  <span className="text-zinc-300">{s.description}</span>
                  <span className="text-zinc-600">({s.tool})</span>
                </div>
              ))}
            </div>
          </div>
        ))}
        {tasks.length === 0 && <div className="text-sm text-zinc-600">No tasks yet.</div>}
      </div>
    </div>
  )
}
