import { type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRightIcon } from '../ui/icons'

interface FeatureCardProps {
  to: string
  title: string
  description: string
  icon: ReactNode
}

export function FeatureCard({ to, title, description, icon }: FeatureCardProps) {
  return (
    <Link
      to={to}
      className="focus-ring group flex flex-col justify-between rounded-card border border-kiwi-shell-50 bg-white p-6 shadow-soft transition hover:-translate-y-0.5 hover:shadow-lift"
    >
      <div>
        <div className="inline-flex rounded-2xl bg-kiwi-flesh-100 p-3 text-kiwi-flesh-700 transition group-hover:bg-kiwi-flesh group-hover:text-white">
          {icon}
        </div>
        <h3 className="mt-4 font-heading text-lg font-semibold text-kiwi-ink">{title}</h3>
        <p className="mt-1.5 text-sm leading-relaxed text-kiwi-ink/55">{description}</p>
      </div>

      <div className="mt-5 flex items-center gap-1.5 text-sm font-semibold text-kiwi-flesh-700">
        Open
        <ArrowRightIcon className="h-4 w-4 transition group-hover:translate-x-1" />
      </div>
    </Link>
  )
}
