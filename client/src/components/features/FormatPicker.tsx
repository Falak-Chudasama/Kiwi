import {
  Archive,
  FileAudio,
  FileImage,
  FileSpreadsheet,
  FileText,
  FileType2,
  FileVideo2,
  Presentation,
} from 'lucide-react'
import { categoryOf, CATEGORY_CLASSES, formatLabel } from './formatUtils'

export interface FormatOption {
  ext: string
  supported: boolean
  reason?: string | null
  category?: string
}

interface FormatPickerProps {
  options: FormatOption[]
  value: string | null
  onChange: (value: string) => void
  /** Group label to promote to the top; it's also pushed to the bottom of the rest. */
  priorityGroup?: string
}

function IconFor({ ext }: { ext: string }) {
  const category = categoryOf(ext)
  const className = 'h-4 w-4'
  if (category === 'pdf') return <FileType2 className={className} />
  if (category === 'image') return <FileImage className={className} />
  if (category === 'spreadsheet') return <FileSpreadsheet className={className} />
  if (category === 'presentation') return <Presentation className={className} />
  if (category === 'audio') return <FileAudio className={className} />
  if (category === 'video') return <FileVideo2 className={className} />
  if (category === 'archive') return <Archive className={className} />
  return <FileText className={className} />
}

const GROUPS = [
  ['Documents', ['pdf', 'docx', 'doc', 'odt', 'rtf', 'txt', 'md', 'html', 'htm', 'epub', 'tex', 'rst', 'org', 'xml']],
  ['Spreadsheets', ['xlsx', 'xls', 'ods', 'csv']],
  ['Presentations', ['pptx', 'ppt', 'odp']],
  ['Images', ['jpg', 'jpeg', 'png', 'webp', 'avif', 'gif', 'bmp', 'tiff', 'tif', 'ico', 'heic', 'heif', 'svg']],
  ['Audio', ['mp3', 'wav', 'flac', 'ogg', 'opus', 'm4a', 'aac', 'wma']],
  ['Video', ['mp4', 'mkv', 'webm', 'avi', 'mov', 'm4v', 'mpeg', 'mpg', '3gp']],
  ['Archives', ['zip', '7z', 'tar']],
] as const

export function FormatPicker({ options, value, onChange, priorityGroup }: FormatPickerProps) {
  const byExt = new Map(options.map((item) => [item.ext, item]))
  // Priority group leads (e.g. Images on the image tools page); Documents,
  // being the least relevant group there, sinks to the bottom.
  const orderedGroups = priorityGroup
    ? [...GROUPS].sort((a, b) => {
        const rank = (label: string) => (label === priorityGroup ? 0 : label === 'Documents' ? 2 : 1)
        return rank(a[0]) - rank(b[0])
      })
    : GROUPS

  return (
    <div className="space-y-6">
      {orderedGroups.map(([label, exts]) => {
        const items = exts.map((ext) => byExt.get(ext)).filter(Boolean) as FormatOption[]
        if (!items.length) return null
        return (
          <section key={label}>
            <div className="mb-2.5 flex items-center gap-2">
              <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-kiwi-ink/35">{label}</span>
              <span className="h-px flex-1 bg-stone-100" />
            </div>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-5">
              {items.map((option) => {
                const active = option.ext === value
                const categoryClass = CATEGORY_CLASSES[categoryOf(option.ext)]
                return (
                  <button
                    key={option.ext}
                    type="button"
                    disabled={!option.supported}
                    onClick={() => onChange(option.ext)}
                    title={option.supported ? undefined : option.reason ?? 'Unavailable'}
                    className={`focus-ring flex items-center gap-2 rounded-xl border px-3 py-2.5 text-left text-sm font-bold transition ${
                      active
                        ? 'border-kiwi-flesh bg-kiwi-flesh text-white shadow-soft'
                        : option.supported
                          ? `${categoryClass} hover:-translate-y-0.5 hover:shadow-soft`
                          : 'cursor-not-allowed border-stone-100 bg-stone-50 text-stone-300 opacity-50'
                    }`}
                  >
                    <span className="shrink-0"><IconFor ext={option.ext} /></span>
                    <span>{formatLabel(option.ext)}</span>
                  </button>
                )
              })}
            </div>
          </section>
        )
      })}
    </div>
  )
}
