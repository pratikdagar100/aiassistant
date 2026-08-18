export interface TranscribeResult {
  text: string
  language: string
  language_name: string
  language_confidence: number
  engine: string
}

export async function transcribeAudio(blob: Blob): Promise<TranscribeResult> {
  const form = new FormData()
  form.append('file', blob, 'recording.webm')
  const res = await fetch('/api/speech/transcribe', { method: 'POST', body: form })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `Transcription failed: ${res.status}`)
  }
  return res.json()
}

export async function synthesizeSpeech(text: string, voice?: string): Promise<Blob> {
  const res = await fetch('/api/speech/synthesize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, voice }),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `Synthesis failed: ${res.status}`)
  }
  return res.blob()
}
