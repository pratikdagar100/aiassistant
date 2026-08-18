import { useEffect, useState } from 'react'
import { listEntities, type EntitySummary } from '../lib/entities'

const MODES = ['disabled', 'enabled', 'confirmation'] as const

export function Permissions() {
  const [entities, setEntities] = useState<EntitySummary[]>([])
  const [entityId, setEntityId] = useState('friday')
  const [perms, setPerms] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    listEntities().then(setEntities).catch(() => setEntities([]))
  }, [])

  async function load() {
    const res = await fetch(`/api/permissions/${entityId}`)
    if (res.ok) setPerms(await res.json())
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entityId])

  async function updateCategory(category: string, mode: string) {
    setSaving(true)
    const next = { ...perms, [category]: mode }
    setPerms(next)
    await fetch(`/api/permissions/${entityId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ permissions: { [category]: mode } }),
    })
    setSaving(false)
  }

  return (
    <div className="flex-1 overflow-y-auto p-8">
      <div className="mb-1 flex items-center gap-3">
        <h1 className="text-2xl font-semibold text-zinc-100">Permissions</h1>
        <select value={entityId} onChange={(e) => setEntityId(e.target.value)} className="rounded border border-zinc-800 bg-zinc-900 px-2 py-1 text-sm text-zinc-200">
          {entities.length === 0 && <option value="friday">friday</option>}
          {entities.map((e) => (
            <option key={e.id} value={e.id}>
              {e.name}
            </option>
          ))}
        </select>
        {saving && <span className="text-xs text-zinc-500">saving…</span>}
      </div>
      <p className="mb-6 text-sm text-zinc-500">
        ADMINISTRATOR is disabled for every entity and cannot be enabled from this UI — PratikAI never bypasses
        Windows security mechanisms.
      </p>

      <div className="overflow-hidden rounded-lg border border-zinc-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-zinc-900 text-zinc-400">
            <tr>
              <th className="px-4 py-2 font-medium">Category</th>
              <th className="px-4 py-2 font-medium">Mode</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(perms).map(([category, mode]) => (
              <tr key={category} className="border-t border-zinc-800">
                <td className="px-4 py-2 font-mono text-xs text-zinc-300">{category}</td>
                <td className="px-4 py-2">
                  <select
                    value={mode}
                    disabled={category === 'ADMINISTRATOR'}
                    onChange={(e) => updateCategory(category, e.target.value)}
                    className="rounded border border-zinc-800 bg-zinc-950 px-2 py-1 text-xs text-zinc-200 disabled:opacity-40"
                  >
                    {MODES.map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
