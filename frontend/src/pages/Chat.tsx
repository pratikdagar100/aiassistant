import { useEffect, useRef, useState } from 'react'
import { listEntities, type EntitySummary } from '../lib/entities'
import { transcribeAudio, synthesizeSpeech } from '../lib/speech'
import { AvatarFace, type AvatarState } from '../components/AvatarFace'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

type SocketState = 'connecting' | 'open' | 'closed'

export function Chat() {
  const [entities, setEntities] = useState<EntitySummary[]>([])
  const [entityId, setEntityId] = useState('friday')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [socketState, setSocketState] = useState<SocketState>('connecting')
  const [conversationId, setConversationId] = useState<number | null>(null)
  const [recording, setRecording] = useState(false)
  const [transcribing, setTranscribing] = useState(false)
  const [detectedLanguage, setDetectedLanguage] = useState<string | null>(null)
  const [voiceReply, setVoiceReply] = useState(false)
  const [speechError, setSpeechError] = useState<string | null>(null)
  const [hasFace, setHasFace] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const streamingTextRef = useRef('')
  const scrollRef = useRef<HTMLDivElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null)

  useEffect(() => {
    listEntities()
      .then(setEntities)
      .catch(() => setEntities([]))
  }, [])

  useEffect(() => {
    fetch(`/api/avatar/${entityId}/status`)
      .then((r) => r.json())
      .then((s) => setHasFace(s.has_face))
      .catch(() => setHasFace(false))
  }, [entityId])

  useEffect(() => {
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${proto}://${window.location.host}/api/chat/ws`)
    wsRef.current = ws

    ws.onopen = () => setSocketState('open')
    ws.onclose = () => setSocketState('closed')

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'chunk') {
        streamingTextRef.current += data.text
        setMessages((prev) => {
          const next = [...prev]
          next[next.length - 1] = { role: 'assistant', content: streamingTextRef.current }
          return next
        })
      } else if (data.type === 'done') {
        setConversationId(data.conversation_id)
        setStreaming(false)
        if (voiceReply && streamingTextRef.current.trim()) {
          playReply(streamingTextRef.current)
        }
        streamingTextRef.current = ''
      } else if (data.type === 'error') {
        setMessages((prev) => {
          const next = [...prev]
          next[next.length - 1] = { role: 'assistant', content: `[error] ${data.detail}` }
          return next
        })
        setStreaming(false)
        streamingTextRef.current = ''
      }
    }

    return () => ws.close()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [voiceReply])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  async function playReply(text: string) {
    try {
      const blob = await synthesizeSpeech(text)
      const url = URL.createObjectURL(blob)
      if (audioPlayerRef.current) {
        audioPlayerRef.current.src = url
        await audioPlayerRef.current.play()
      }
    } catch (err) {
      setSpeechError(err instanceof Error ? err.message : 'TTS playback failed')
    }
  }

  function switchEntity(id: string) {
    setEntityId(id)
    setConversationId(null)
    setMessages([])
  }

  function send(text?: string) {
    const message = (text ?? input).trim()
    if (!message || !wsRef.current || socketState !== 'open' || streaming) return

    setMessages((prev) => [...prev, { role: 'user', content: message }, { role: 'assistant', content: '' }])
    setInput('')
    setStreaming(true)
    streamingTextRef.current = ''

    wsRef.current.send(JSON.stringify({ entity_id: entityId, conversation_id: conversationId, message }))
  }

  async function toggleRecording() {
    if (recording) {
      mediaRecorderRef.current?.stop()
      setRecording(false)
      return
    }

    setSpeechError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      audioChunksRef.current = []
      recorder.ondataavailable = (e) => audioChunksRef.current.push(e.data)
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        setTranscribing(true)
        try {
          const result = await transcribeAudio(blob)
          setInput(result.text)
          setDetectedLanguage(result.language_name)
        } catch (err) {
          setSpeechError(err instanceof Error ? err.message : 'Transcription failed')
        } finally {
          setTranscribing(false)
        }
      }
      mediaRecorderRef.current = recorder
      recorder.start()
      setRecording(true)
    } catch (err) {
      setSpeechError(err instanceof Error ? err.message : 'Microphone access denied')
    }
  }

  const activeEntity = entities.find((e) => e.id === entityId)
  const avatarState: AvatarState = recording ? 'listening' : transcribing ? 'thinking' : streaming ? 'speaking' : 'idle'

  return (
    <div className="flex flex-1 flex-col p-8">
      <audio ref={audioPlayerRef} className="hidden" />
      <div className="mb-1 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <AvatarFace entityId={entityId} hasFace={hasFace} state={avatarState} size={56} />
          <h1 className="text-2xl font-semibold text-zinc-100">Live Chat</h1>
          <select
            value={entityId}
            onChange={(e) => switchEntity(e.target.value)}
            className="rounded border border-zinc-800 bg-zinc-900 px-2 py-1 text-sm text-zinc-200"
          >
            {entities.length === 0 && <option value="friday">friday</option>}
            {entities.map((e) => (
              <option key={e.id} value={e.id}>
                {e.name}
              </option>
            ))}
          </select>
          <label className="flex items-center gap-1.5 text-xs text-zinc-400">
            <input type="checkbox" checked={voiceReply} onChange={(e) => setVoiceReply(e.target.checked)} />
            Voice reply
          </label>
        </div>
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
            socketState === 'open'
              ? 'bg-emerald-500/15 text-emerald-400'
              : socketState === 'connecting'
                ? 'bg-amber-500/15 text-amber-400'
                : 'bg-red-500/15 text-red-400'
          }`}
        >
          {socketState}
        </span>
      </div>
      <p className="mb-6 text-sm text-zinc-500">
        {activeEntity?.model ?? 'qwen3:8b'} · memory {activeEntity?.memory_enabled === false ? 'disabled' : 'enabled'}
        {detectedLanguage && <> · last heard: {detectedLanguage}</>}
      </p>

      {speechError && (
        <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">{speechError}</div>
      )}

      <div ref={scrollRef} className="mb-4 flex-1 space-y-3 overflow-y-auto rounded-lg border border-zinc-800 bg-zinc-900 p-4">
        {messages.length === 0 && <div className="text-sm text-zinc-600">Say hello to {activeEntity?.name ?? 'Friday'}.</div>}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[75%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm ${
                m.role === 'user' ? 'bg-violet-600 text-white' : 'bg-zinc-800 text-zinc-100'
              }`}
            >
              {m.content || (streaming && i === messages.length - 1 ? '…' : '')}
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <button
          onClick={toggleRecording}
          disabled={transcribing}
          title="Push to talk"
          className={`rounded-lg px-3 py-2 text-sm font-medium disabled:opacity-40 ${
            recording ? 'bg-red-600 text-white' : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700'
          }`}
        >
          {recording ? '● Stop' : transcribing ? '…' : '🎤'}
        </button>
        <input
          className="flex-1 rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-violet-500"
          placeholder="Type a message, or use the mic…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          disabled={socketState !== 'open' || streaming}
        />
        <button
          onClick={() => send()}
          disabled={socketState !== 'open' || streaming || !input.trim()}
          className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
        >
          Send
        </button>
      </div>
    </div>
  )
}
