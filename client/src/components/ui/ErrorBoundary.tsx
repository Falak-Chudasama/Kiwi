import React, { Component, type ErrorInfo, type ReactNode } from 'react'
import { AlertCircle, RotateCcw, Home } from 'lucide-react'

interface Props {
  children: ReactNode
  fallbackTitle?: string
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[ErrorBoundary caught error]:', error, errorInfo)
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  private handleReload = () => {
    window.location.reload()
  }

  private handleGoHome = () => {
    this.setState({ hasError: false, error: null })
    window.location.href = '/'
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="mx-auto w-full max-w-2xl px-4 py-16 text-center">
          <div className="glass-panel rounded-3xl p-8 sm:p-10 shadow-lift border border-rose-200/60 dark:border-rose-900/40">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-rose-100 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400">
              <AlertCircle className="h-7 w-7" />
            </div>
            <h2 className="text-xl sm:text-2xl font-extrabold text-stone-900 dark:text-stone-50">
              {this.props.fallbackTitle || 'Workspace Error Encountered'}
            </h2>
            <p className="mt-2 text-sm text-stone-600 dark:text-stone-400 max-w-md mx-auto leading-relaxed">
              {this.state.error?.message || 'An unexpected error occurred while rendering this view.'}
            </p>

            <div className="mt-7 flex flex-wrap items-center justify-center gap-3">
              <button
                type="button"
                onClick={this.handleReload}
                className="btn-glass-primary flex items-center gap-2"
              >
                <RotateCcw className="h-4 w-4" />
                <span>Reload Page</span>
              </button>
              <button
                type="button"
                onClick={this.handleGoHome}
                className="flex items-center gap-2 rounded-full border border-stone-200/90 dark:border-white/[0.08] bg-white/70 dark:bg-[#1C1D18]/70 px-5 py-2.5 text-sm font-bold text-stone-700 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-[#22231E] transition"
              >
                <Home className="h-4 w-4" />
                <span>Back to Home</span>
              </button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
