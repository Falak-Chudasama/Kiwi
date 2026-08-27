import { type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRightIcon } from '../ui/icons'

interface FeatureCardProps {
  to: string
  title: string
  description: string
  icon: ReactNode
  tone: 'green' | 'blue' | 'red' | 'violet' | 'orange'
}

const TONES = {
  green: {
    glow: 'bg-lime-100/80', icon: 'bg-lime-50 text-lime-700 group-hover:bg-lime-600 group-hover:text-white', edge: 'hover:border-lime-200', arrow: 'text-lime-700',
  },
  blue: {
    glow: 'bg-sky-100/80', icon: 'bg-sky-50 text-sky-700 group-hover:bg-sky-600 group-hover:text-white', edge: 'hover:border-sky-200', arrow: 'text-sky-700',
  },
  red: {
    glow: 'bg-rose-100/80', icon: 'bg-rose-50 text-rose-700 group-hover:bg-rose-600 group-hover:text-white', edge: 'hover:border-rose-200', arrow: 'text-rose-700',
  },
  violet: {
    glow: 'bg-violet-100/80', icon: 'bg-violet-50 text-violet-700 group-hover:bg-violet-600 group-hover:text-white', edge: 'hover:border-violet-200', arrow: 'text-violet-700',
  },
  orange: {
    glow: 'bg-orange-100/80', icon: 'bg-orange-50 text-orange-700 group-hover:bg-orange-600 group-hover:text-white', edge: 'hover:border-orange-200', arrow: 'text-orange-700',
  },
}

export function FeatureCard({ to, title, description, icon, tone }: FeatureCardProps) {
  const style = TONES[tone]
  return (
    <Link
      to={to}
      className={`focus-ring group relative flex min-h-64 overflow-hidden rounded-[2rem] border border-stone-200 bg-white p-7 shadow-soft transition duration-200 hover:-translate-y-1 hover:shadow-lift ${style.edge}`}
    >
      <div className={`absolute -right-10 -top-10 h-32 w-32 rounded-full blur-2xl ${style.glow}`} />
      <div className="relative flex w-full flex-col justify-between">
        <div>
          <div className={`inline-flex rounded-2xl p-3.5 transition ${style.icon}`}>{icon}</div>
          <h3 className="mt-5 font-heading text-xl font-bold tracking-tight text-kiwi-ink">{title}</h3>
          <p className="mt-2 text-sm leading-6 text-kiwi-ink/55">{description}</p>
        </div>
        <div className={`mt-7 flex items-center gap-1.5 text-sm font-bold ${style.arrow}`}>
          Open tool <ArrowRightIcon className="h-4 w-4 transition group-hover:translate-x-1" />
        </div>
      </div>
    </Link>
  )
}
