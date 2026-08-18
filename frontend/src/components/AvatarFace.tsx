export type AvatarState = 'idle' | 'listening' | 'thinking' | 'speaking'

const RING_STYLES: Record<AvatarState, string> = {
  idle: 'ring-zinc-700',
  listening: 'ring-emerald-500 animate-pulse',
  thinking: 'ring-amber-500',
  speaking: 'ring-violet-500 animate-pulse',
}

const LABEL: Record<AvatarState, string> = {
  idle: 'Idle',
  listening: 'Listening…',
  thinking: 'Thinking…',
  speaking: 'Speaking…',
}

interface Props {
  entityId: string
  hasFace: boolean
  state: AvatarState
  size?: number
}

/**
 * Static-image avatar with a state-driven ring/animation — the documented
 * fallback for real-time lip sync (MuseTalk isn't bundled; see docs/avatar.md
 * and app/avatar/musetalk.py). Reflects actual mic/streaming state, not a
 * decorative loop.
 */
export function AvatarFace({ entityId, hasFace, state, size = 96 }: Props) {
  return (
    <div className="flex flex-col items-center gap-1.5">
      <div
        className={`overflow-hidden rounded-full bg-zinc-800 ring-4 transition-all duration-300 ${RING_STYLES[state]}`}
        style={{ width: size, height: size }}
      >
        {hasFace ? (
          <img src={`/api/avatar/${entityId}/face`} alt="" className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-2xl text-zinc-500">
            {entityId.slice(0, 1).toUpperCase()}
          </div>
        )}
      </div>
      <span className="text-xs text-zinc-500">{LABEL[state]}</span>
    </div>
  )
}
