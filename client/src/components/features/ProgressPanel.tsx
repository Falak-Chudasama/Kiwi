import { SpinnerIcon } from '../ui/icons'

interface ProgressPanelProps {
  label: string
  progress: number
  onCancel?: () => void
}

export function ProgressPanel({ label, progress, onCancel }: ProgressPanelProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="rounded-2xl border border-black/[0.06] bg-white p-5 shadow-soft animate-scale-in"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5 text-xs font-semibold text-stone-900">
          <SpinnerIcon className="h-4 w-4 animate-spin text-kiwi-flesh-600" />
          <span>{label}</span>
        </div>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="text-[11px] font-semibold text-stone-400 transition hover:text-stone-700"
          >
            Cancel
          </button>
        )}
      </div>

      <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-stone-100">
        <div
          className="h-full rounded-full bg-kiwi-flesh transition-all duration-300"
          style={{ width: `${Math.max(progress, 6)}%` }}
        />
      </div>
    </div>
  )
}
