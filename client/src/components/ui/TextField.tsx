import type { InputHTMLAttributes } from 'react'

export function TextField(props: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className="focus-ring w-full rounded-xl border border-kiwi-shell-50 bg-white px-4 py-2.5 text-sm text-kiwi-ink placeholder:text-kiwi-ink/35 focus:border-kiwi-flesh"
    />
  )
}
