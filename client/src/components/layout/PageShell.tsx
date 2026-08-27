import { type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeftIcon } from '../ui/icons'

interface PageShellProps {
  title: string
  description: string
  icon: ReactNode
  children: ReactNode
}

export function PageShell({ title, description, icon, children }: PageShellProps) {
  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-10 sm:px-6">
      <Link
        to="/"
        className="focus-ring inline-flex items-center gap-1.5 rounded-lg text-sm font-medium text-kiwi-ink/50 transition hover:text-kiwi-ink"
      >
        <ArrowLeftIcon className="h-4 w-4" />
        Back to Kiwi
      </Link>

      <div className="mt-5 flex items-center gap-3.5">
        <div className="rounded-2xl bg-kiwi-flesh-100 p-3 text-kiwi-flesh-700">{icon}</div>
        <div>
          <h1 className="font-heading text-2xl font-bold text-kiwi-ink">{title}</h1>
          <p className="mt-0.5 text-sm text-kiwi-ink/50">{description}</p>
        </div>
      </div>

      <div className="mt-8">{children}</div>
    </main>
  )
}
