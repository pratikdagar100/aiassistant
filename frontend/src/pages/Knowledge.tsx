import { useEffect, useRef, useState } from 'react'

interface Doc {
  id: number
  filename: string
  file_type: string
  status: string
  error_message: string | null
  chunk_count: number
  uploaded_at: string
}

const ENTITY_ID = 'friday'

export function Knowledge() {
  const [docs, setDocs] = useState<Doc[]>([])
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<{ content: string }[]>([])
  const fileInput = useRef<HTMLInputElement>(null)

  async function load() {
    const res = await fetch(`/api/knowledge?entity_id=${ENTITY_ID}`)
    if (res.ok) setDocs(await res.json())
  }

  useEffect(() => {
    load()
  }, [])

  async function upload(file: File) {
    setUploading(true)
    setError(null)
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`/api/knowledge/upload?entity_id=${ENTITY_ID}`, { method: 'POST', body: form })
    const body = await res.json()
    setUploading(false)
    if (!res.ok) {
      setError(body.detail ?? `Error ${res.status}`)
      return
    }
    load()
  }

  async function remove(id: number) {
    await fetch(`/api/knowledge/${id}`, { method: 'DELETE' })
    load()
  }

  async function search() {
    if (!query.trim()) return
    const res = await fetch('/api/knowledge/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entity_id: ENTITY_ID, query }),
    })
    if (res.ok) setResults(await res.json())
  }

  return (
    <div className="flex-1 overflow-y-auto p-8">
      <h1 className="mb-1 text-2xl font-semibold text-zinc-100">Knowledge — {ENTITY_ID}</h1>
      <p className="mb-6 text-sm text-zinc-500">
        Documents indexed here are retrieved automatically during chat when relevant — no need to reference them
        explicitly.
      </p>

      <div className="mb-6 flex gap-2">
        <input
          ref={fileInput}
          type="file"
          accept=".txt,.md,.pdf,.docx,.csv,.py,.js,.ts,.json"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0]
            if (f) upload(f)
            e.target.value = ''
          }}
        />
        <button
          onClick={() => fileInput.current?.click()}
          disabled={uploading}
          className="rounded bg-violet-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
        >
          {uploading ? 'Uploading…' : 'Upload Document'}
        </button>
      </div>
      {error && <div className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">{error}</div>}

      <div className="mb-8 space-y-2">
        {docs.length === 0 && <div className="text-sm text-zinc-600">No documents yet.</div>}
        {docs.map((d) => (
          <div key={d.id} className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900 p-3">
            <div className="text-sm">
              <span className="text-zinc-200">{d.filename}</span>
              <span className="ml-2 text-xs text-zinc-500">{d.chunk_count} chunks</span>
              {d.status === 'error' && <span className="ml-2 text-xs text-red-400">{d.error_message}</span>}
            </div>
            <button onClick={() => remove(d.id)} className="text-xs text-red-400 hover:text-red-300">
              delete
            </button>
          </div>
        ))}
      </div>

      <h2 className="mb-2 text-sm font-medium text-zinc-300">Test search</h2>
      <div className="mb-4 flex gap-2">
        <input
          className="input flex-1"
          placeholder="Ask something covered by your documents…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && search()}
        />
        <button onClick={search} className="rounded bg-zinc-800 px-4 py-2 text-sm text-zinc-200">
          Search
        </button>
      </div>
      <div className="space-y-2">
        {results.map((r, i) => (
          <div key={i} className="rounded-lg border border-zinc-800 bg-zinc-900 p-3 text-xs text-zinc-300">
            {r.content}
          </div>
        ))}
      </div>
    </div>
  )
}
