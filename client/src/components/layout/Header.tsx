import { Link, NavLink } from 'react-router-dom'
import {
  Archive,
  ArrowRightLeft,
  FileText,
  Image as ImageIcon,
  Minimize2,
} from 'lucide-react'
import kiwiIcon from '../../assets/kiwi-icon.svg'

const NAV_ITEMS = [
  { to: '/convert', label: 'Convert', icon: ArrowRightLeft },
  { to: '/images', label: 'Images', icon: ImageIcon },
  { to: '/pdf', label: 'PDF', icon: FileText },
  { to: '/compress', label: 'Compress', icon: Minimize2 },
  { to: '/archives', label: 'Archives', icon: Archive },
]

export function Header() {
  return (
    <>
      {/* Desktop Floating Navigation Capsule */}
      <header className="sticky top-4 z-40 mx-auto hidden w-full max-w-4xl px-4 sm:block">
        <div className="glass-capsule flex items-center justify-between gap-3 rounded-full px-5 py-3 shadow-floating">
          {/* Brand Wordmark & Logo */}
          <Link
            to="/"
            className="focus-ring flex items-center gap-2.5 rounded-full pr-2 transition hover:opacity-90"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white p-1 shadow-2xs border border-black/[0.05]">
              <img src={kiwiIcon} alt="Kiwi" className="h-7 w-7 object-contain" />
            </div>
            <span className="font-display text-base font-extrabold text-stone-900 tracking-tight">
              Kiwi
            </span>
          </Link>

          {/* Nav Links */}
          <nav className="flex items-center gap-1.5" aria-label="Primary Desktop Navigation">
            {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `focus-ring flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold transition ${
                    isActive
                      ? 'bg-stone-900 text-white shadow-xs'
                      : 'text-stone-600 hover:bg-stone-100 hover:text-stone-900'
                  }`
                }
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      {/* Mobile Top Header Bar */}
      <header className="sticky top-0 z-40 flex items-center justify-between border-b border-black/[0.05] bg-white/95 px-5 py-3.5 backdrop-blur-md sm:hidden">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white p-0.5 shadow-2xs border border-black/[0.05]">
            <img src={kiwiIcon} alt="Kiwi" className="h-6 w-6 object-contain" />
          </div>
          <span className="font-display text-base font-extrabold text-stone-900">Kiwi</span>
        </Link>
        <span className="text-xs font-semibold text-stone-500">Offline Workspace</span>
      </header>

      {/* Mobile Floating Bottom Dock (5 Primary Tools) */}
      <nav
        className="fixed bottom-3 inset-x-3 z-50 flex justify-around rounded-2xl border border-black/[0.08] bg-white/95 py-2.5 px-2 shadow-lift backdrop-blur-lg sm:hidden"
        aria-label="Primary Mobile Navigation"
      >
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex flex-col items-center gap-1 rounded-xl px-3 py-1.5 text-xs font-semibold transition ${
                isActive
                  ? 'text-kiwi-flesh-700 bg-kiwi-flesh/10 font-bold'
                  : 'text-stone-500 hover:text-stone-900'
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
