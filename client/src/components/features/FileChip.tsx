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
    <div className="flex items-center gap-3.5 rounded-2xl border border-stone-200/90 dark:border-white/[0.08] bg-white dark:bg-[#181915] px-4 py-3 shadow-xs transition hover:border-stone-300 dark:hover:border-stone-700">
      <div className={`flex h-11 w-11 shrink-0 flex-col items-center justify-center rounded-xl border text-[10px] font-bold ${CATEGORY_CLASSES[category]}`}>
        <Icon className="h-4 w-4" />
        {ext ? <span className="mt-0.5 leading-none uppercase">{formatLabel(ext).slice(0, 4)}</span> : null}
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm sm:text-base font-bold text-stone-900 dark:text-stone-100">{name}</p>
        <p className="text-xs sm:text-sm text-stone-500 dark:text-stone-400">{sizeLabel}</p>
      </div>
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          aria-label={`Remove ${name}`}
          className="focus-ring rounded-xl p-2 text-stone-400 transition hover:bg-rose-50 dark:hover:bg-rose-950/40 hover:text-rose-600 dark:hover:text-rose-400"
        >
          <TrashIcon className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}
