import { useEffect, type ReactNode } from 'react'
import { CloseIcon } from './icons'

interface PopupProps {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
  footer?: ReactNode
  width?: 'sm' | 'md' | 'lg'
}

const widthClass: Record<NonNullable<PopupProps['width']>, string> = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-xl',
}

export function Popup({ open, onClose, title, children, footer, width = 'md' }: PopupProps) {
  useEffect(() => {
    if (!open) return
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = ''
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      <div
        className="absolute inset-0 bg-kiwi-ink/40 backdrop-blur-sm animate-fade-in"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="popup-title"
        className={`relative w-full ${widthClass[width]} rounded-card border border-kiwi-shell-50 bg-white p-6 shadow-lift animate-pop-in`}
      >
        <div className="flex items-start justify-between gap-4">
          <h2 id="popup-title" className="font-heading text-lg font-semibold text-kiwi-ink">
            {title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="focus-ring rounded-full p-1.5 text-kiwi-ink/50 transition hover:bg-kiwi-flesh-50 hover:text-kiwi-ink"
          >
            <CloseIcon className="h-4.5 w-4.5" />
          </button>
        </div>

        <div className="mt-4 text-sm text-kiwi-ink/75">{children}</div>

        {footer ? <div className="mt-6 flex justify-end gap-3">{footer}</div> : null}
      </div>
    </div>
  )
}
