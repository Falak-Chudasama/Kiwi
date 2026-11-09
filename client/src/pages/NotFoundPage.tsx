import { Link } from 'react-router-dom'
import { ArrowLeft, FileQuestion } from 'lucide-react'

export default function NotFoundPage() {
  return (
    <main className="mx-auto flex min-h-[60vh] w-full max-w-xl flex-col items-center justify-center px-4 py-16 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-300 border border-black/[0.04] dark:border-white/[0.08] mb-4 shadow-xs">
        <FileQuestion className="h-7 w-7 text-stone-700 dark:text-stone-200" />
      </div>

      <h1 className="font-display text-2xl font-bold tracking-tight text-stone-900 dark:text-stone-50 sm:text-3xl">
        Page Not Found
      </h1>
      <p className="mt-2 text-sm sm:text-base text-stone-600 dark:text-stone-400 font-sans max-w-sm leading-relaxed">
        The tool or workspace you requested does not exist or has been moved.
      </p>

      <Link
        to="/"
        className="focus-ring mt-6 inline-flex items-center gap-2 rounded-2xl bg-stone-900 dark:bg-stone-100 px-6 py-3.5 text-sm font-bold text-white dark:text-stone-900 shadow-soft transition hover:bg-black dark:hover:bg-white"
      >
        <ArrowLeft className="h-4 w-4" />
        <span>Return to Workspace</span>
      </Link>
    </main>
  )
}

