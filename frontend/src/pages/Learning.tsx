import { useEffect, useState } from 'react'

interface Dashboard {
  total_conversations: number
  total_memories: number
  potential_training_examples: number
  approved_examples: number
  rejected_examples: number
  dataset_size: number
  last_training: string | null
  model_adapter_status: string
}

interface Example {
  id: number
  input_text: string
  output_text: string
  category: string
  status: string
  created_at: string
}

const ENTITY_ID = 'friday'

export function Learning() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null)
  const [pending, setPending] = useState<Example[]>([])

  async function load() {
    const [dRes, eRes] = await Promise.all([
      fetch(`/api/learning/dashboard?entity_id=${ENTITY_ID}`),
      fetch(`/api/learning/examples?entity_id=${ENTITY_ID}&status=pending`),
    ])
    if (dRes.ok) setDashboard(await dRes.json())
    if (eRes.ok) setPending(await eRes.json())
  }

  useEffect(() => {
    load()
    const interval = setInterval(load, 6000)
    return () => clearInterval(interval)
  }, [])

  async function act(id: number, action: 'approve' | 'reject') {
    await fetch(`/api/learning/examples/${id}/${action}`, { method: 'POST' })
    load()
  }

  return (
    <div className="flex-1 overflow-y-auto p-8">
      <h1 className="mb-1 text-2xl font-semibold text-zinc-100">Learning</h1>
      <p className="mb-6 text-sm text-zinc-500">
        Corrections and preferences detected in conversation, staged for review. Nothing here trains anything until
        you approve it and build a dataset (Training page).
      </p>

      {dashboard && (
        <div className="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <Stat label="Conversations" value={dashboard.total_conversations} />
          <Stat label="Memories" value={dashboard.total_memories} />
          <Stat label="Pending review" value={dashboard.potential_training_examples} />
          <Stat label="Approved" value={dashboard.approved_examples} />
          <Stat label="Rejected" value={dashboard.rejected_examples} />
          <Stat label="Dataset size" value={dashboard.dataset_size} />
        </div>
      )}

      <h2 className="mb-2 text-sm font-medium text-zinc-300">Review queue</h2>
      <div className="space-y-3">
        {pending.length === 0 && <div className="text-sm text-zinc-600">Nothing pending.</div>}
        {pending.map((e) => (
          <div key={e.id} className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
            <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] text-zinc-400">{e.category}</span>
            <div className="mt-2 text-xs text-zinc-500">User said:</div>
            <div className="text-sm text-zinc-200">{e.input_text}</div>
            <div className="mt-2 text-xs text-zinc-500">Ideal response:</div>
            <div className="text-sm text-zinc-200">{e.output_text}</div>
            <div className="mt-3 flex justify-end gap-2">
              <button onClick={() => act(e.id, 'approve')} className="rounded bg-emerald-600 px-3 py-1 text-xs font-medium text-white">
                Approve
              </button>
              <button onClick={() => act(e.id, 'reject')} className="rounded bg-red-600 px-3 py-1 text-xs font-medium text-white">
                Reject
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-3">
      <div className="text-lg font-semibold text-zinc-100">{value}</div>
      <div className="text-[10px] text-zinc-500">{label}</div>
    </div>
  )
}
