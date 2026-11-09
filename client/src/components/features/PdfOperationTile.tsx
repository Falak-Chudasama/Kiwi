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
          ? 'border-kiwi-flesh bg-kiwi-flesh text-white shadow-soft dark:border-kiwi-lime dark:bg-kiwi-flesh'
          : 'border-stone-200/90 dark:border-white/[0.08] bg-white dark:bg-[#181915] text-stone-700 dark:text-stone-300 hover:border-kiwi-flesh/40 dark:hover:border-kiwi-lime/40 hover:text-stone-900 dark:hover:text-stone-100 shadow-2xs'
      }`}
    >
      {icon}
      <span className="text-xs font-semibold">{label}</span>
    </button>
  )
}
