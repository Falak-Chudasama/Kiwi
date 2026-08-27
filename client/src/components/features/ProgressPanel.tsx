import { SpinnerIcon } from '../ui/icons'

interface ProgressPanelProps {
  label: string
  progress: number
}

export function ProgressPanel({ label, progress }: ProgressPanelProps) {
  return (
    <div className="rounded-2xl border border-kiwi-shell-50 bg-white px-5 py-4">
      <div className="flex items-center gap-2.5 text-sm font-medium text-kiwi-ink">
        <SpinnerIcon className="h-4 w-4 animate-spin text-kiwi-flesh" />
        {label}
      </div>
      <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-kiwi-flesh-50">
        <div
          className="h-full rounded-full bg-kiwi-flesh transition-all duration-500"
          style={{ width: `${Math.max(progress, 6)}%` }}
        />
      </div>
    </div>
  )
}
