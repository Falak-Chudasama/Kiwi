import { Link, NavLink } from 'react-router-dom'
import {
  Archive,
  ArrowRightLeft,
  FileText,
  Image as ImageIcon,
  Minimize2,
  Moon,
  Sun,
} from 'lucide-react'
import kiwiIcon from '../../assets/kiwi-icon.svg'
import { useTheme } from '../ui/ThemeProvider'

const NAV_ITEMS = [
  { to: '/convert', label: 'Convert', icon: ArrowRightLeft },
  { to: '/images', label: 'Images', icon: ImageIcon },
  { to: '/pdf', label: 'PDF', icon: FileText },
  { to: '/compress', label: 'Compress', icon: Minimize2 },
  { to: '/archives', label: 'Archives', icon: Archive },
]

export function Header() {
  const { isDark, toggleTheme } = useTheme()

  return (
    <>
      {/* Desktop Floating Navigation Capsule */}
      <header className="sticky top-4 z-40 mx-auto hidden w-full max-w-4xl px-4 sm:block">
        <div className="glass-capsule flex items-center justify-between gap-3 rounded-full px-5 py-3 shadow-floating transition-colors duration-200">
          {/* Brand Wordmark & Logo */}
          <Link
            to="/"
            className="focus-ring flex items-center gap-2.5 rounded-full pr-2 transition hover:opacity-90"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white dark:bg-stone-800 p-1 shadow-2xs border border-black/[0.05] dark:border-white/[0.08]">
              <img src={kiwiIcon} alt="Kiwi" className="h-7 w-7 object-contain" />
            </div>
            <span className="font-display text-base font-extrabold text-stone-900 dark:text-white tracking-tight">
              Kiwi
            </span>
          </Link>

          {/* Nav Links + Theme Switcher */}
          <nav className="flex items-center gap-1.5" aria-label="Primary Desktop Navigation">
            {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `focus-ring flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold transition ${
                    isActive
                      ? 'bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-xs'
                      : 'text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 hover:text-stone-900 dark:hover:text-white'
                  }`
                }
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
              </NavLink>
            ))}

            <div className="mx-1 h-5 w-px bg-stone-200 dark:bg-stone-700" aria-hidden="true" />

            {/* Dark/Light Mode Switcher */}
            <button
              type="button"
              onClick={toggleTheme}
              className="focus-ring flex h-9 w-9 items-center justify-center rounded-full text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 transition"
              aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
              title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {isDark ? (
                <Sun className="h-4.5 w-4.5 text-kiwi-lime transition-transform duration-200 hover:rotate-45" />
              ) : (
                <Moon className="h-4.5 w-4.5 text-stone-600 transition-transform duration-200 hover:-rotate-12" />
              )}
            </button>
          </nav>
        </div>
      </header>

      {/* Mobile Top Header Bar */}
      <header className="sticky top-0 z-40 flex items-center justify-between border-b border-black/[0.05] dark:border-white/[0.08] bg-white/95 dark:bg-[#181915]/95 px-5 py-3.5 backdrop-blur-md transition-colors duration-200 sm:hidden">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white dark:bg-stone-800 p-0.5 shadow-2xs border border-black/[0.05] dark:border-white/[0.08]">
            <img src={kiwiIcon} alt="Kiwi" className="h-6 w-6 object-contain" />
          </div>
          <span className="font-display text-base font-extrabold text-stone-900 dark:text-white">Kiwi</span>
        </Link>
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-stone-500 dark:text-stone-400">Offline Workspace</span>
          <button
            type="button"
            onClick={toggleTheme}
            className="focus-ring flex h-8 w-8 items-center justify-center rounded-full text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 transition"
            aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDark ? (
              <Sun className="h-4 w-4 text-kiwi-lime" />
            ) : (
              <Moon className="h-4 w-4 text-stone-600" />
            )}
          </button>
        </div>
      </header>

      {/* Mobile Floating Bottom Dock (5 Primary Tools) */}
      <nav
        className="fixed bottom-3 inset-x-3 z-50 flex justify-around rounded-2xl border border-black/[0.08] dark:border-white/[0.08] bg-white/95 dark:bg-[#181915]/95 py-2.5 px-2 shadow-lift backdrop-blur-lg transition-colors duration-200 sm:hidden"
        aria-label="Primary Mobile Navigation"
      >
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex flex-col items-center gap-1 rounded-xl px-3 py-1.5 text-xs font-semibold transition ${
                isActive
                  ? 'text-kiwi-flesh dark:text-kiwi-lime bg-kiwi-flesh/10 dark:bg-kiwi-lime/10 font-bold'
                  : 'text-stone-500 dark:text-stone-400 hover:text-stone-900 dark:hover:text-stone-100'
              }`
            }
          >
            <Icon className="h-5 w-5" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </>
  )
}
