export interface EntitySummary {
  id: string
  name: string
  description: string | null
  personality: string | null
  system_prompt: string | null
  model: string
  language_mode: string
  memory_enabled: boolean
  computer_access: boolean
  autonomy_level: number
  face_path: string | null
  voice_id: string | null
  is_active: boolean
  created_at: string
  last_active_at: string | null
}

export interface Preset {
  key: string
  label: string
  personality: string
  system_prompt: string
}

export interface CreateEntityInput {
  id: string
  name: string
  description?: string
  personality?: string
  system_prompt?: string
  model?: string
  language_mode?: string
  memory_enabled?: boolean
  computer_access?: boolean
  autonomy_level?: number
}

export async function listEntities(): Promise<EntitySummary[]> {
  const res = await fetch('/api/entities')
  if (!res.ok) throw new Error(`Failed to list entities: ${res.status}`)
  return res.json()
}

export async function getPresets(): Promise<Preset[]> {
  const res = await fetch('/api/entities/presets')
  if (!res.ok) throw new Error(`Failed to load presets: ${res.status}`)
  return res.json()
}

export async function createEntity(input: CreateEntityInput): Promise<EntitySummary> {
  const res = await fetch('/api/entities', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `Failed to create entity: ${res.status}`)
  }
  return res.json()
}

export async function deleteEntity(id: string, purge = false): Promise<void> {
  const res = await fetch(`/api/entities/${id}?purge=${purge}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`Failed to delete entity: ${res.status}`)
}

export async function getEntityStats(id: string): Promise<Record<string, number>> {
  const res = await fetch(`/api/entities/${id}/stats`)
  if (!res.ok) throw new Error(`Failed to load stats: ${res.status}`)
  return res.json()
}
