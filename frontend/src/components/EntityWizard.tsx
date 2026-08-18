import { useEffect, useState } from 'react'
import { createEntity, getPresets, type Preset } from '../lib/entities'

const STEPS = ['Preset', 'Identity', 'Personality', 'Model & Language', 'Memory & Autonomy', 'Review'] as const

interface Props {
  onClose: () => void
  onCreated: () => void
}

export function EntityWizard({ onClose, onCreated }: Props) {
  const [step, setStep] = useState(0)
  const [presets, setPresets] = useState<Preset[]>([])
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const [id, setId] = useState('')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [personality, setPersonality] = useState('')
  const [systemPrompt, setSystemPrompt] = useState('')
  const [model, setModel] = useState('qwen3:8b')
  const [languageMode, setLanguageMode] = useState('auto')
  const [memoryEnabled, setMemoryEnabled] = useState(true)
  const [computerAccess, setComputerAccess] = useState(false)
  const [autonomyLevel, setAutonomyLevel] = useState(0)

  useEffect(() => {
    getPresets().then(setPresets).catch(() => setPresets([]))
  }, [])

  function applyPreset(p: Preset) {
    setPersonality(p.personality)
    setSystemPrompt(p.system_prompt)
    setStep(1)
  }

  const idValid = /^[a-z0-9][a-z0-9_-]{0,63}$/.test(id)
  const canProceedIdentity = idValid && name.trim().length > 0

  async function submit() {
    setSubmitting(true)
    setError(null)
    try {
      await createEntity({
        id,
        name,
        description: description || undefined,
        personality: personality || undefined,
        system_prompt: systemPrompt || undefined,
        model,
        language_mode: languageMode,
        memory_enabled: memoryEnabled,
        computer_access: computerAccess,
        autonomy_level: autonomyLevel,
      })
      onCreated()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create entity')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-10 flex items-center justify-center bg-black/60 p-4">
      <div className="flex max-h-[85vh] w-full max-w-2xl flex-col rounded-xl border border-zinc-800 bg-zinc-950">
        <div className="flex items-center justify-between border-b border-zinc-800 px-6 py-4">
          <h2 className="text-lg font-semibold text-zinc-100">Create Entity — {STEPS[step]}</h2>
          <button onClick={onClose} className="text-zinc-500 hover:text-zinc-300">
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          {step === 0 && (
            <div className="grid grid-cols-2 gap-3">
              {presets.map((p) => (
                <button
                  key={p.key}
                  onClick={() => applyPreset(p)}
                  className="rounded-lg border border-zinc-800 bg-zinc-900 p-4 text-left hover:border-violet-600"
                >
                  <div className="font-medium text-zinc-100">{p.label}</div>
                  <div className="mt-1 text-xs text-zinc-500 line-clamp-2">{p.personality || 'No preset personality'}</div>
                </button>
              ))}
            </div>
          )}

          {step === 1 && (
            <div className="space-y-4">
              <Field label="Entity ID (slug, lowercase, used internally)">
                <input
                  className="input"
                  value={id}
                  onChange={(e) => setId(e.target.value.toLowerCase())}
                  placeholder="jarvis"
                />
                {id && !idValid && <p className="mt-1 text-xs text-red-400">lowercase letters, numbers, - and _ only</p>}
              </Field>
              <Field label="Name">
                <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Jarvis" />
              </Field>
              <Field label="Description">
                <textarea
                  className="input"
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="What is this entity for?"
                />
              </Field>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <Field label="Personality">
                <textarea className="input" rows={3} value={personality} onChange={(e) => setPersonality(e.target.value)} />
              </Field>
              <Field label="System prompt">
                <textarea className="input" rows={5} value={systemPrompt} onChange={(e) => setSystemPrompt(e.target.value)} />
              </Field>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <Field label="Model (Ollama tag)">
                <input className="input" value={model} onChange={(e) => setModel(e.target.value)} />
              </Field>
              <Field label="Language mode">
                <select className="input" value={languageMode} onChange={(e) => setLanguageMode(e.target.value)}>
                  <option value="auto">Auto-detect (multilingual)</option>
                  <option value="en">English only</option>
                </select>
              </Field>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-4">
              <Toggle label="Memory enabled" checked={memoryEnabled} onChange={setMemoryEnabled} />
              <Toggle
                label="Computer access (has no effect until Phase 6's permission system lands)"
                checked={computerAccess}
                onChange={setComputerAccess}
              />
              <Field label={`Autonomy level: ${autonomyLevel}`}>
                <input
                  type="range"
                  min={0}
                  max={10}
                  value={autonomyLevel}
                  onChange={(e) => setAutonomyLevel(Number(e.target.value))}
                  className="w-full"
                />
              </Field>
            </div>
          )}

          {step === 5 && (
            <div className="space-y-2 text-sm text-zinc-300">
              <ReviewRow label="ID" value={id} />
              <ReviewRow label="Name" value={name} />
              <ReviewRow label="Description" value={description || '—'} />
              <ReviewRow label="Model" value={model} />
              <ReviewRow label="Language mode" value={languageMode} />
              <ReviewRow label="Memory" value={memoryEnabled ? 'enabled' : 'disabled'} />
              <ReviewRow label="Computer access" value={computerAccess ? 'enabled' : 'disabled'} />
              <ReviewRow label="Autonomy" value={String(autonomyLevel)} />
            </div>
          )}

          {error && <div className="mt-4 rounded bg-red-500/10 p-3 text-sm text-red-400">{error}</div>}
        </div>

        <div className="flex items-center justify-between border-t border-zinc-800 px-6 py-4">
          <button
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            disabled={step === 0}
            className="rounded px-3 py-1.5 text-sm text-zinc-400 disabled:opacity-30"
          >
            Back
          </button>
          {step < STEPS.length - 1 ? (
            <button
              onClick={() => setStep((s) => s + 1)}
              disabled={step === 1 && !canProceedIdentity}
              className="rounded bg-violet-600 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-40"
            >
              Next
            </button>
          ) : (
            <button
              onClick={submit}
              disabled={submitting}
              className="rounded bg-violet-600 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-40"
            >
              {submitting ? 'Creating…' : 'Create Entity'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-zinc-400">{label}</span>
      {children}
    </label>
  )
}

function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="flex items-center gap-2 text-sm text-zinc-300">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      {label}
    </label>
  )
}

function ReviewRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between border-b border-zinc-900 py-1.5">
      <span className="text-zinc-500">{label}</span>
      <span className="max-w-[60%] truncate text-right">{value}</span>
    </div>
  )
}
