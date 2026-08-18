import { useEffect, useState } from 'react'

interface AuditEntry {
  id: number
  entity_id: string | null
  timestamp: string
  tool: string | null
  parameters: Record<string, unknown> | null
  result: string | null
  risk_level: string | null
  approval_required: boolean
  approved: boolean | null
  success: boolean | null
}

export function Audit() {
  const [entries, setEntries] = useState<AuditEntry[]>([])

  async function load() {
    const res = await fetch('/api/audit')
    if (res.ok) setEntries(await res.json())
  }

  useEffect(() => {
    load()
    const interval = setInterval(load, 5000)
    return () => clearInterval(interval)
  }, [])

  function statusBadge(e: AuditEntry) {
    if (e.approval_required && e.approved === null) return <span className="text-amber-400">pending</span>
    if (e.approved === false) return <span className="text-red-400">denied</span>
    if (e.success === true) return <span className="text-emerald-400">success</span>
    if (e.success === false) return <span className="text-red-400">failed</span>
    return <span className="text-zinc-500">—</span>
  }

  return (
    <div className="flex-1 overflow-y-auto p-8">
      <h1 className="mb-1 text-2xl font-semibold text-zinc-100">Audit Log</h1>
      <p className="mb-6 text-sm text-zinc-500">Every computer-tool call, whether it ran immediately or needed approval.</p>

      <div className="overflow-x-auto rounded-lg border border-zinc-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-zinc-900 text-zinc-400">
            <tr>
              <th className="px-3 py-2 font-medium">Time</th>
              <th className="px-3 py-2 font-medium">Entity</th>
              <th className="px-3 py-2 font-medium">Tool</th>
              <th className="px-3 py-2 font-medium">Risk</th>
              <th className="px-3 py-2 font-medium">Status</th>
              <th className="px-3 py-2 font-medium">Result</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e) => (
              <tr key={e.id} className="border-t border-zinc-800 text-zinc-300">
                <td className="px-3 py-2 text-xs text-zinc-500">{new Date(e.timestamp).toLocaleTimeString()}</td>
                <td className="px-3 py-2 text-xs">{e.entity_id}</td>
                <td className="px-3 py-2 font-mono text-xs">{e.tool}</td>
                <td className="px-3 py-2 text-xs">{e.risk_level}</td>
                <td className="px-3 py-2 text-xs">{statusBadge(e)}</td>
                <td className="max-w-xs truncate px-3 py-2 text-xs text-zinc-500">{e.result}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
