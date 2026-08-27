import { FileGenericIcon, FileArchiveIcon, FileImageIcon, FileSpreadsheetIcon, FileTextIcon, PresentationIcon, TrashIcon } from '../ui/icons'
import { categoryOf, CATEGORY_CLASSES, extensionOf, formatLabel } from './formatUtils'

interface FileChipProps {
  name: string
  sizeLabel: string
  onRemove?: () => void
}

const ICONS = {
  pdf: FileTextIcon,
  image: FileImageIcon,
  document: FileTextIcon,
  spreadsheet: FileSpreadsheetIcon,
  presentation: PresentationIcon,
  archive: FileArchiveIcon,
  text: FileTextIcon,
  audio: FileGenericIcon,
  video: FileGenericIcon,
  generic: FileGenericIcon,
} as const

export function FileChip({ name, sizeLabel, onRemove }: FileChipProps) {
  const category = categoryOf(name)
  const Icon = ICONS[category]
  const ext = extensionOf(name)
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-stone-200 bg-white px-4 py-3 shadow-[0_5px_20px_-14px_rgba(48,48,48,.3)]">
      <div className={`flex h-11 w-11 shrink-0 flex-col items-center justify-center rounded-xl border text-[10px] font-bold ${CATEGORY_CLASSES[category]}`}>
        <Icon className="h-4 w-4" />
        {ext ? <span className="mt-0.5">{formatLabel(ext)}</span> : null}
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold text-kiwi-ink">{name}</p>
        <p className="text-xs text-kiwi-ink/45">{sizeLabel}</p>
      </div>
      {onRemove ? (
        <button type="button" onClick={onRemove} aria-label={`Remove ${name}`} className="focus-ring rounded-lg p-1.5 text-kiwi-ink/35 transition hover:bg-red-50 hover:text-red-500">
          <TrashIcon className="h-4 w-4" />
        </button>
      ) : null}
    </div>
  )
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}
