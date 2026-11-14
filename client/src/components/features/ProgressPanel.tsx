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
      className="glass-panel rounded-2xl p-5 shadow-soft animate-scale-in"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5 text-xs font-semibold text-stone-900 dark:text-stone-100">
          <SpinnerIcon className="h-4 w-4 animate-spin text-kiwi-flesh-600 dark:text-kiwi-lime" />
          <span>{label}</span>
        </div>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="text-[11px] font-semibold text-stone-400 dark:text-stone-500 transition hover:text-stone-700 dark:hover:text-stone-300"
          >
            Cancel
          </button>
        )}
      </div>

      <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-stone-100 dark:bg-stone-800">
        <div
          className="h-full rounded-full bg-kiwi-flesh dark:bg-kiwi-lime transition-all duration-300"
          style={{ width: `${Math.max(progress, 6)}%` }}
        />
      </div>
    </div>
  )
}
