import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'
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
  success: <CheckCircleIcon className="h-4 w-4 text-emerald-600 shrink-0" />,
  error: <AlertCircleIcon className="h-4 w-4 text-rose-600 shrink-0" />,
  info: <AlertCircleIcon className="h-4 w-4 text-kiwi-flesh-700 shrink-0" />,
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

  const contextValue = useMemo(() => ({ push }), [push])

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      <div
        className="pointer-events-none fixed bottom-5 right-5 z-[70] flex w-full max-w-sm flex-col gap-2.5 px-4 sm:px-0"
        aria-live="polite"
      >
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role="alert"
            className="pointer-events-auto flex items-start gap-3 rounded-2xl border border-black/[0.06] bg-white/95 px-4 py-3 text-sm text-stone-900 shadow-lift backdrop-blur-md animate-slide-up"
          >
            {iconByKind[toast.kind]}
            <span className="flex-1 text-xs font-medium leading-relaxed">{toast.message}</span>
            <button
              type="button"
              onClick={() => dismiss(toast.id)}
              aria-label="Dismiss notice"
              className="rounded-lg p-1 text-stone-400 transition hover:bg-stone-100 hover:text-stone-700"
            >
              <CloseIcon className="h-3 w-3" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}
