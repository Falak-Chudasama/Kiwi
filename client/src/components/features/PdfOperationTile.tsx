import { type ReactNode } from 'react'

interface PdfOperationTileProps {
  label: string
  icon: ReactNode
  active: boolean
  onClick: () => void
}

export function PdfOperationTile({ label, icon, active, onClick }: PdfOperationTileProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`focus-ring flex flex-col items-center gap-2 rounded-2xl border px-3 py-4 text-center transition ${
        active
          ? 'border-kiwi-flesh bg-kiwi-flesh text-white shadow-soft'
          : 'border-kiwi-shell-50 bg-white text-kiwi-ink/70 hover:border-kiwi-flesh/40 hover:text-kiwi-ink'
      }`}
    >
      {icon}
      <span className="text-xs font-semibold">{label}</span>
    </button>
  )
}
