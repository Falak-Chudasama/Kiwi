interface FormatPickerProps {
  options: string[]
  value: string | null
  onChange: (ext: string) => void
}

export function FormatPicker({ options, value, onChange }: FormatPickerProps) {
  if (!options.length) return null

  return (
    <div className="flex flex-wrap gap-2">
      {options.map((ext) => {
        const active = value === ext
        return (
          <button
            key={ext}
            type="button"
            onClick={() => onChange(ext)}
            className={`focus-ring rounded-xl border px-4 py-2 text-sm font-semibold uppercase tracking-wide transition ${
              active
                ? 'border-kiwi-flesh bg-kiwi-flesh text-white shadow-soft'
                : 'border-kiwi-shell-50 bg-white text-kiwi-ink/70 hover:border-kiwi-flesh/40 hover:text-kiwi-ink'
            }`}
          >
            {ext}
          </button>
        )
      })}
    </div>
  )
}
