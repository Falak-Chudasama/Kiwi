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
    <main className="mx-auto w-full max-w-4xl px-4 py-9 sm:px-6 sm:py-12">
      <Link to="/" className="focus-ring inline-flex items-center gap-1.5 rounded-lg text-sm font-medium text-kiwi-ink/50 transition hover:text-kiwi-ink">
        <ArrowLeftIcon className="h-4 w-4" />
        Home
      </Link>

      <div className="mt-5 flex items-start gap-3.5">
        <div className="rounded-2xl bg-kiwi-flesh-100 p-3 text-kiwi-flesh-700">{icon}</div>
        <div>
          <h1 className="font-heading text-2xl font-bold tracking-tight text-kiwi-ink sm:text-3xl">{title}</h1>
          <p className="mt-1 text-sm leading-6 text-kiwi-ink/50">{description}</p>
        </div>
      </div>

      <div className="mt-8">{children}</div>
    </main>
  )
}
