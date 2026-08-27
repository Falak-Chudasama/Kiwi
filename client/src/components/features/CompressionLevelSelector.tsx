export type CompressionLevel = 'low' | 'medium' | 'high' | 'extreme'

interface LevelOption {
  value: CompressionLevel
  label: string
  hint: string
}

const LEVELS: LevelOption[] = [
  { value: 'low', label: 'Low', hint: 'Best quality' },
  { value: 'medium', label: 'Medium', hint: 'Balanced' },
  { value: 'high', label: 'High', hint: 'Smaller size' },
  { value: 'extreme', label: 'Extreme', hint: 'Smallest size' },
]

interface CompressionLevelSelectorProps {
  value: CompressionLevel
  onChange: (level: CompressionLevel) => void
}

export function CompressionLevelSelector({ value, onChange }: CompressionLevelSelectorProps) {
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
      {LEVELS.map((level) => {
        const active = value === level.value
        return (
          <button
            key={level.value}
            type="button"
            onClick={() => onChange(level.value)}
            className={`focus-ring rounded-2xl border px-3 py-3 text-left transition ${
              active
                ? 'border-kiwi-flesh bg-kiwi-flesh text-white shadow-soft'
                : 'border-kiwi-shell-50 bg-white text-kiwi-ink hover:border-kiwi-flesh/40'
            }`}
          >
            <div className="font-heading text-sm font-semibold">{level.label}</div>
            <div className={`text-xs ${active ? 'text-white/80' : 'text-kiwi-ink/45'}`}>
              {level.hint}
            </div>
          </button>
        )
      })}
    </div>
  )
}
