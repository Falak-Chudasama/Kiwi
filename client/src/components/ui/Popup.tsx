import { useEffect, type ReactNode } from 'react'
import { CloseIcon } from './icons'

interface PopupProps { open: boolean; onClose: () => void; title: string; children: ReactNode; footer?: ReactNode; width?: 'sm' | 'md' | 'lg' }
const widthClass = { sm: 'max-w-sm', md: 'max-w-md', lg: 'max-w-xl' } as const

export function Popup({ open, onClose, title, children, footer, width = 'md' }: PopupProps) {
  useEffect(() => {
    if (!open) return
    const onKeyDown = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', onKeyDown); document.body.style.overflow = 'hidden'
    return () => { document.removeEventListener('keydown', onKeyDown); document.body.style.overflow = '' }
  }, [open, onClose])
  if (!open) return null
  return <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
    <div className="absolute inset-0 bg-kiwi-ink/45 backdrop-blur-sm animate-fade-in" onClick={onClose} />
    <div role="dialog" aria-modal="true" aria-labelledby="popup-title" className={`relative max-h-[90vh] w-full overflow-auto ${widthClass[width]} rounded-[2rem] border border-stone-200 dark:border-white/[0.08] bg-white dark:bg-[#181915] p-6 shadow-lift animate-pop-in`}>
      <div className="flex items-start justify-between gap-4"><h2 id="popup-title" className="font-heading text-xl font-bold text-stone-900 dark:text-stone-100">{title}</h2><button type="button" onClick={onClose} aria-label="Close" className="focus-ring rounded-full p-1.5 text-stone-400 dark:text-stone-500 hover:bg-stone-50 dark:hover:bg-stone-800 hover:text-stone-900 dark:hover:text-stone-100"><CloseIcon className="h-5 w-5" /></button></div>
      <div className="mt-5 text-sm text-stone-600 dark:text-stone-300">{children}</div>
      {footer ? <div className="mt-6 flex justify-end gap-3">{footer}</div> : null}
    </div>
  </div>
}
