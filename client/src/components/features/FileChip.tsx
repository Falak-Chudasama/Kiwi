import { FileGenericIcon, TrashIcon } from '../ui/icons'

interface FileChipProps {
  name: string
  sizeLabel: string
  onRemove?: () => void
}

export function FileChip({ name, sizeLabel, onRemove }: FileChipProps) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-kiwi-shell-50 bg-white px-4 py-3">
      <div className="rounded-xl bg-kiwi-flesh-50 p-2">
        <FileGenericIcon className="h-4.5 w-4.5 text-kiwi-flesh-700" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-kiwi-ink">{name}</p>
        <p className="text-xs text-kiwi-ink/45">{sizeLabel}</p>
      </div>
      {onRemove ? (
        <button
          type="button"
          onClick={onRemove}
          aria-label={`Remove ${name}`}
          className="focus-ring rounded-lg p-1.5 text-kiwi-ink/35 transition hover:bg-red-50 hover:text-red-500"
        >
          <TrashIcon className="h-4 w-4" />
        </button>
      ) : null}
    </div>
  )
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
