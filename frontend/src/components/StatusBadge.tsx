const COLORS: Record<string, string> = {
  READY: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  WARNING: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  ERROR: 'bg-red-500/15 text-red-400 border-red-500/30',
  UNKNOWN: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
}

export function StatusBadge({ status }: { status: string }) {
  const cls = COLORS[status] ?? COLORS.UNKNOWN
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${cls}`}>
      {status}
    </span>
  )
}
