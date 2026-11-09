import type { InputHTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

export function TextField({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={cn(
        'focus-ring w-full rounded-xl border border-stone-200/90 bg-white px-4 py-3 text-sm sm:text-base text-stone-900 placeholder:text-stone-400 transition hover:border-stone-300 focus:border-kiwi-flesh',
        className,
      )}
    />
  )
}
