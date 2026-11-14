import type { InputHTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

export function TextField({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={cn(
        'focus-ring w-full rounded-xl border border-black/[0.08] dark:border-white/[0.10] glass-card px-4 py-3 text-sm sm:text-base text-stone-900 dark:text-stone-100 placeholder:text-stone-400 dark:placeholder:text-stone-500 transition hover:border-stone-300 dark:hover:border-stone-700 focus:border-kiwi-flesh dark:focus:border-kiwi-lime',
        className,
      )}
    />
  )
}
