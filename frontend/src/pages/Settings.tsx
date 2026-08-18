import { useEffect, useState } from 'react'

interface SettingsValues {
  startup_enabled: boolean
  auto_select_entity: boolean
  auto_mic: boolean
  wake_word: boolean
  auto_avatar: boolean
  default_entity: string
  startup_task_registered: boolean
  app_version: string
  phase: number
}

export function Settings() {
  const [values, setValues] = useState<SettingsValues | null>(null)
  const [saving, setSaving] = useState(false)

  async function load() {
    const res = await fetch('/api/settings')
    if (res.ok) setValues(await res.json())
  }

  useEffect(() => {
    load()
  }, [])

  async function update(key: string, value: unknown) {
    setSaving(true)
    await fetch('/api/settings', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ values: { [key]: value } }),
    })
    await load()
    setSaving(false)
  }

  if (!values) return <div className="flex-1 p-8 text-sm text-zinc-500">Loading…</div>

  return (
    <div className="flex-1 overflow-y-auto p-8">
      <h1 className="mb-1 text-2xl font-semibold text-zinc-100">Settings</h1>
      <p className="mb-6 text-sm text-zinc-500">
        PratikAI v{values.app_version} · Phase {values.phase}
        {saving && ' · saving…'}
      </p>

      <div className="mb-6 rounded-lg border border-zinc-800 bg-zinc-900 p-4">
        <h2 className="mb-3 text-sm font-medium text-zinc-300">Windows startup</h2>
        <p className="mb-3 text-xs text-zinc-500">
          Managed via a visible Task Scheduler entry, not a hidden registry key. Toggle it from a terminal, not this
          checkbox, so the action is always explicit:
        </p>
        <div className="mb-3 flex items-center gap-2 text-xs">
          <span className={values.startup_task_registered ? 'text-emerald-400' : 'text-zinc-500'}>
            {values.startup_task_registered ? 'Registered — PratikAI starts at login' : 'Not registered'}
          </span>
        </div>
        <code className="block rounded bg-black/30 p-2 text-xs text-zinc-400">
          scripts\register_startup.ps1 {'   '}# enable
          <br />
          scripts\unregister_startup.ps1 {'  '}# disable
        </code>
      </div>

      <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
        <h2 className="mb-3 text-sm font-medium text-zinc-300">Startup behavior</h2>
        <div className="space-y-3">
          <Toggle label="Auto-select default entity on launch" checked={values.auto_select_entity} onChange={(v) => update('auto_select_entity', v)} />
          <Toggle label="Auto-enable microphone on launch" checked={values.auto_mic} onChange={(v) => update('auto_mic', v)} />
          <Toggle
            label="Wake word listening (not yet implemented — toggling this has no effect yet)"
            checked={values.wake_word}
            onChange={(v) => update('wake_word', v)}
          />
          <Toggle label="Auto-show avatar on launch" checked={values.auto_avatar} onChange={(v) => update('auto_avatar', v)} />
        </div>
      </div>
    </div>
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
