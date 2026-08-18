import { useEffect, useRef, useState } from 'react'
import { deleteEntity, listEntities, type EntitySummary } from '../lib/entities'
import { EntityWizard } from '../components/EntityWizard'
import { AvatarFace } from '../components/AvatarFace'

export function Entities() {
  const [entities, setEntities] = useState<EntitySummary[]>([])
  const [faceVersion, setFaceVersion] = useState(0) // bump to force <img> re-fetch after upload
  const [error, setError] = useState<string | null>(null)
  const [showWizard, setShowWizard] = useState(false)
  const fileInputs = useRef<Record<string, HTMLInputElement | null>>({})

  async function load() {
    try {
      setEntities(await listEntities())
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function handleDelete(id: string) {
    if (id === 'friday') {
      alert('Friday is the default entity and cannot be deleted from this view.')
      return
    }
    if (!confirm(`Delete entity "${id}"? This soft-deletes it (data is kept).`)) return
    await deleteEntity(id, false)
    load()
  }

  async function handleFaceUpload(id: string, file: File) {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`/api/avatar/${id}/face`, { method: 'POST', body: form })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      alert(body.detail ?? 'Face upload failed')
      return
    }
    setFaceVersion((v) => v + 1)
    load()
  }

  return (
    <div className="flex-1 overflow-y-auto p-8">
      <div className="mb-1 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-100">Entities</h1>
        <button
          onClick={() => setShowWizard(true)}
          className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white"
        >
          + New Entity
        </button>
      </div>
      <p className="mb-6 text-sm text-zinc-500">
        Each entity has isolated memory, its own personality, and its own permissions.
      </p>

      {error && (
        <div className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">{error}</div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {entities.map((e) => (
          <div key={e.id} className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
            <div className="flex items-start gap-3">
              <button
                onClick={() => fileInputs.current[e.id]?.click()}
                title="Click to change face"
                className="shrink-0"
              >
                <AvatarFace key={faceVersion} entityId={e.id} hasFace={!!e.face_path} state="idle" size={48} />
              </button>
              <input
                ref={(el) => {
                  fileInputs.current[e.id] = el
                }}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                className="hidden"
                onChange={(ev) => {
                  const file = ev.target.files?.[0]
                  if (file) handleFaceUpload(e.id, file)
                  ev.target.value = ''
                }}
              />
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-zinc-100">{e.name}</span>
                  <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] text-zinc-400">{e.id}</span>
                </div>
                {e.description && <p className="mt-1 text-xs text-zinc-500">{e.description}</p>}
              </div>
            </div>
            <div className="mt-3 flex flex-wrap gap-1.5 text-[10px]">
              <Badge label={`model: ${e.model}`} />
              <Badge label={`lang: ${e.language_mode}`} />
              <Badge label={e.memory_enabled ? 'memory on' : 'memory off'} />
              <Badge label={`autonomy ${e.autonomy_level}`} />
            </div>
            <div className="mt-3 flex justify-end">
              <button onClick={() => handleDelete(e.id)} className="text-xs text-red-400 hover:text-red-300">
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {showWizard && <EntityWizard onClose={() => setShowWizard(false)} onCreated={load} />}
    </div>
  )
}

function Badge({ label }: { label: string }) {
  return <span className="rounded-full border border-zinc-700 px-2 py-0.5 text-zinc-400">{label}</span>
}
