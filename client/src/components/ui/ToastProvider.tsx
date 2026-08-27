import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'
import { AlertCircleIcon, CheckCircleIcon, CloseIcon } from './icons'

type ToastKind = 'success' | 'error' | 'info'

interface Toast {
  id: string
  kind: ToastKind
  message: string
}

interface ToastContextValue {
  push: (kind: ToastKind, message: string) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}

const iconByKind: Record<ToastKind, ReactNode> = {
  success: <CheckCircleIcon className="h-4.5 w-4.5 text-kiwi-flesh" />,
  error: <AlertCircleIcon className="h-4.5 w-4.5 text-red-500" />,
  info: <AlertCircleIcon className="h-4.5 w-4.5 text-kiwi-zest-600" />,
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const push = useCallback(
    (kind: ToastKind, message: string) => {
      const id = crypto.randomUUID()
      setToasts((prev) => [...prev, { id, kind, message }])
      window.setTimeout(() => dismiss(id), 4200)
    },
    [dismiss],
  )

  return (
    <ToastContext.Provider value={{ push }}>
      {children}
      <div className="pointer-events-none fixed bottom-5 right-5 z-[60] flex w-full max-w-sm flex-col gap-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className="pointer-events-auto flex items-start gap-2.5 rounded-2xl border border-kiwi-shell-50 bg-white px-4 py-3 text-sm text-kiwi-ink shadow-lift animate-slide-up"
          >
            {iconByKind[toast.kind]}
            <span className="flex-1">{toast.message}</span>
            <button
              type="button"
              onClick={() => dismiss(toast.id)}
              aria-label="Dismiss"
              className="text-kiwi-ink/40 transition hover:text-kiwi-ink"
            >
              <CloseIcon className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}
