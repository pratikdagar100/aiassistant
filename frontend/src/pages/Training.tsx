import { useEffect, useState } from 'react'

interface EnvStatus {
  ready: boolean
  missing_packages: string[]
  install_hint: string | null
  free_disk_gb: number
  disk_warning: string | null
}

const ENTITY_ID = 'friday'

export function Training() {
  const [env, setEnv] = useState<EnvStatus | null>(null)
  const [datasetResult, setDatasetResult] = useState<{ path: string; example_count: number } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [building, setBuilding] = useState(false)

  useEffect(() => {
    fetch('/api/training/environment')
      .then((r) => r.json())
      .then(setEnv)
  }, [])

  async function buildDataset() {
    setBuilding(true)
    setError(null)
    const res = await fetch(`/api/training/dataset/${ENTITY_ID}`, { method: 'POST' })
    const body = await res.json()
    setBuilding(false)
    if (!res.ok) {
      setError(body.detail ?? `Error ${res.status}`)
      return
    }
    setDatasetResult(body)
  }

  return (
    <div className="flex-1 overflow-y-auto p-8">
      <h1 className="mb-1 text-2xl font-semibold text-zinc-100">Training</h1>
      <p className="mb-6 text-sm text-zinc-500">
        LoRA/QLoRA personalization is optional and never runs automatically. Build a dataset from approved examples
        here, then run <code className="rounded bg-black/30 px-1">scripts\train_lora.ps1</code> manually — it
        defaults to a dry run that validates everything without downloading or training anything.
      </p>

      <div className="mb-6 rounded-lg border border-zinc-800 bg-zinc-900 p-4">
        <h2 className="mb-2 text-sm font-medium text-zinc-300">1. Build dataset from approved examples</h2>
        <button onClick={buildDataset} disabled={building} className="rounded bg-violet-600 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-40">
          {building ? 'Building…' : 'Build Dataset'}
        </button>
        {error && <div className="mt-3 rounded bg-red-500/10 p-2 text-xs text-red-400">{error}</div>}
        {datasetResult && (
          <div className="mt-3 text-xs text-zinc-400">
            Wrote {datasetResult.example_count} examples to <code className="rounded bg-black/30 px-1">{datasetResult.path}</code>
          </div>
        )}
      </div>

      <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
        <h2 className="mb-2 text-sm font-medium text-zinc-300">2. Training environment</h2>
        {env ? (
          <div className="space-y-1 text-xs">
            <div className={env.ready ? 'text-emerald-400' : 'text-amber-400'}>
              {env.ready ? 'Ready to train' : 'Not ready — missing packages'}
            </div>
            {env.missing_packages.length > 0 && (
              <div className="text-zinc-500">
                Missing: {env.missing_packages.join(', ')}
                <br />
                Install: <code className="rounded bg-black/30 px-1">{env.install_hint}</code>
              </div>
            )}
            <div className="text-zinc-500">Free disk: {env.free_disk_gb} GB</div>
            {env.disk_warning && <div className="text-amber-400">{env.disk_warning}</div>}
          </div>
        ) : (
          <div className="text-xs text-zinc-600">Checking…</div>
        )}
      </div>
    </div>
  )
}
