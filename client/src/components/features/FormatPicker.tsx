import { useMemo, useState } from 'react'
import {
  Archive,
  Check,
  FileAudio,
  FileImage,
  FileSpreadsheet,
  FileText,
  FileType2,
  FileVideo2,
  Presentation,
  Search,
  X,
} from 'lucide-react'
import { categoryOf, formatLabel } from './formatUtils'

export interface FormatOption {
  ext: string
  supported: boolean
  ready?: boolean
  status?: 'ready' | 'requires_engine' | 'degraded_or_lossy' | 'content_dependent' | 'unsupported'
  reason?: string | null
  category?: string
  strategy?: string | null
  fidelity?: string | null
}

interface FormatPickerProps {
  options: FormatOption[]
  value: string | null
  onChange: (value: string) => void
  priorityGroup?: string
}

function IconFor({ ext }: { ext: string }) {
  const category = categoryOf(ext)
  const className = 'h-4 w-4 shrink-0'
  if (category === 'pdf') return <FileType2 className={className} />
  if (category === 'image') return <FileImage className={className} />
  if (category === 'spreadsheet') return <FileSpreadsheet className={className} />
  if (category === 'presentation') return <Presentation className={className} />
  if (category === 'audio') return <FileAudio className={className} />
  if (category === 'video') return <FileVideo2 className={className} />
  if (category === 'archive') return <Archive className={className} />
  return <FileText className={className} />
}

const CATEGORIES = [
  'All',
  'Documents',
  'Images',
  'Spreadsheets',
  'Presentations',
  'Media',
  'Archives',
] as const

const GROUPS = [
  ['Documents', ['pdf', 'docx', 'doc', 'odt', 'rtf', 'txt', 'md', 'html', 'epub', 'tex', 'rst', 'org', 'xml']],
  ['Images', ['jpg', 'jpeg', 'png', 'webp', 'avif', 'gif', 'bmp', 'tiff', 'ico', 'heic', 'svg']],
  ['Spreadsheets', ['xlsx', 'xls', 'ods', 'csv']],
  ['Presentations', ['pptx', 'ppt', 'odp']],
  ['Media', ['mp3', 'wav', 'flac', 'ogg', 'opus', 'm4a', 'aac', 'mp4', 'mkv', 'webm', 'mov']],
  ['Archives', ['zip', '7z', 'tar']],
] as const

export function FormatPicker({ options, value, onChange, priorityGroup }: FormatPickerProps) {
  const [search, setSearch] = useState('')
  const [activeCategory, setActiveCategory] = useState<string>('All')

  const byExt = useMemo(() => new Map(options.map((item) => [item.ext.toLowerCase(), item])), [options])

  const filteredGroups = useMemo(() => {
    const query = search.trim().toLowerCase()

    return GROUPS.map(([label, exts]) => {
      // Filter by category tab
      if (activeCategory !== 'All') {
        if (activeCategory === 'Media' && label !== 'Media') return null
        if (activeCategory !== 'Media' && label !== activeCategory) return null
      }

      // Filter by search query
      const matchingExts = exts.filter((ext) => {
        if (!query) return true
        const option = byExt.get(ext)
        return (
          ext.toLowerCase().includes(query) ||
          (option?.reason && option.reason.toLowerCase().includes(query)) ||
          (option?.strategy && option.strategy.toLowerCase().includes(query))
        )
      })

      const items = matchingExts.map((ext) => byExt.get(ext)).filter(Boolean) as FormatOption[]
      if (!items.length) return null

      return { label, items }
    }).filter(Boolean) as { label: string; items: FormatOption[] }[]
  }, [byExt, search, activeCategory])

  return (
    <div className="space-y-5">
      {/* Search and Category Filter Tray */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400 dark:text-stone-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search formats (e.g. webp, docx, pdf)..."
            className="focus-ring w-full rounded-xl border border-stone-200/90 dark:border-white/[0.08] glass-card pl-11 pr-10 py-2.5 text-sm sm:text-base text-stone-900 dark:text-stone-100 placeholder:text-stone-400 dark:placeholder:text-stone-500 transition hover:border-stone-300 dark:hover:border-stone-700 focus:border-kiwi-flesh dark:focus:border-kiwi-lime"
          />
          {search && (
            <button
              type="button"
              onClick={() => setSearch('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-stone-400 dark:text-stone-500 hover:text-stone-700 dark:hover:text-stone-300"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Category Pills */}
        <div className="flex flex-wrap items-center gap-1.5">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => setActiveCategory(cat)}
              className={`rounded-xl px-3 py-1.5 text-xs sm:text-sm font-semibold transition ${
                activeCategory === cat
                  ? 'bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-xs'
                  : 'text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 hover:text-stone-900 dark:hover:text-white'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Format Grid Groups */}
      {filteredGroups.length === 0 ? (
        <div className="rounded-xl border border-dashed border-stone-200 dark:border-stone-800 py-10 text-center text-sm text-stone-400 dark:text-stone-500">
          No formats match &ldquo;{search}&rdquo;.
        </div>
      ) : (
        <div className="space-y-5">
          {filteredGroups.map(({ label, items }) => (
            <div key={label}>
              <div className="mb-2.5 flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-stone-500 dark:text-stone-400">
                  {label}
                </span>
                <span className="h-px flex-1 bg-stone-200/70 dark:bg-stone-800" />
              </div>

              <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
                {items.map((opt) => {
                  const isSelected = opt.ext === value
                  const isAvailable = opt.supported && opt.ready !== false
                  const requiresEngine = opt.supported && opt.ready === false

                  return (
                    <button
                      key={opt.ext}
                      type="button"
                      disabled={!isAvailable}
                      onClick={() => onChange(opt.ext)}
                      title={opt.reason || undefined}
                      className={`group relative flex items-center justify-between rounded-xl border p-3 text-left text-sm transition ${
                        isSelected
                          ? 'border-kiwi-flesh bg-kiwi-flesh text-white shadow-soft ring-2 ring-kiwi-flesh/20 font-bold dark:border-kiwi-lime dark:bg-kiwi-flesh dark:ring-kiwi-lime/30'
                          : isAvailable
                            ? 'border-stone-200/90 dark:border-white/[0.08] glass-card text-stone-800 dark:text-stone-200 hover:border-kiwi-flesh/50 dark:hover:border-kiwi-lime/50 hover:bg-white/45 dark:hover:bg-white/[0.05] shadow-2xs'
                            : 'cursor-not-allowed border-stone-100 dark:border-stone-800/60 bg-stone-50/50 dark:bg-[#141512]/50 text-stone-300 dark:text-stone-600 opacity-60'
                      }`}
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <IconFor ext={opt.ext} />
                        <span className="font-semibold truncate text-sm">{formatLabel(opt.ext)}</span>
                      </div>

                      {isSelected ? (
                        <Check className="h-4 w-4 shrink-0 text-white" />
                      ) : requiresEngine ? (
                        <span className="text-[10px] font-semibold text-amber-700 dark:text-amber-400 bg-amber-100/70 dark:bg-amber-950/60 rounded px-1.5 py-0.5">
                          Engine
                        </span>
                      ) : opt.status === 'content_dependent' ? (
                        <span className="text-[10px] font-medium text-stone-400 dark:text-stone-400 bg-stone-100 dark:bg-stone-800 rounded px-1.5 py-0.5">
                          Tables
                        </span>
                      ) : null}
                    </button>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
