import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import {
  Archive,
  ArrowRightLeft,
  Camera,
  FileText,
  Image as ImageIcon,
  Minimize2,
  Moon,
  Sun,
} from 'lucide-react'
import kiwiIcon from '../../assets/kiwi-icon.svg'
import { useTheme } from '../ui/ThemeProvider'
import { useKeyboardNav } from '../../hooks/useKeyboardNav'

const NAV_ITEMS = [
  { to: '/convert', label: 'Convert', icon: ArrowRightLeft },
  { to: '/scan', label: 'Scan', icon: Camera },
  { to: '/images', label: 'Images', icon: ImageIcon },
  { to: '/pdf', label: 'PDF', icon: FileText },
  { to: '/compress', label: 'Compress', icon: Minimize2 },
  { to: '/archives', label: 'Archives', icon: Archive },
]

export function Header() {
  const { isDark, toggleTheme } = useTheme()
  const location = useLocation()
  useKeyboardNav()
  const navContainerRef = useRef<HTMLDivElement>(null)
  const itemRefs = useRef<Record<string, HTMLAnchorElement | null>>({})
  const [pillStyle, setPillStyle] = useState<{
    left: number
    top: number
    width: number
    height: number
    opacity: number
  }>({ left: 0, top: 0, width: 0, height: 0, opacity: 0 })
  const [isReady, setIsReady] = useState(false)

  const updatePill = () => {
    const activeItem = NAV_ITEMS.find((item) =>
      location.pathname === item.to ||
      (item.to === '/convert' && location.pathname === '/documents') ||
      (item.to === '/scan' && location.pathname === '/scanner')
    )

    if (activeItem && itemRefs.current[activeItem.to] && navContainerRef.current) {
      const navRect = navContainerRef.current.getBoundingClientRect()
      const elRect = itemRefs.current[activeItem.to]!.getBoundingClientRect()

      setPillStyle({
        left: elRect.left - navRect.left,
        top: elRect.top - navRect.top,
        width: elRect.width,
        height: elRect.height,
        opacity: 1,
      })
    } else {
      setPillStyle((prev) => ({ ...prev, opacity: 0 }))
    }
  }

  useEffect(() => {
    updatePill()
    const timer = setTimeout(() => {
      setIsReady(true)
    }, 50)
    window.addEventListener('resize', updatePill)
    return () => {
      clearTimeout(timer)
      window.removeEventListener('resize', updatePill)
    }
  }, [location.pathname])

  return (
    <>
      {/* Desktop Floating Navigation Capsule - Absolute / Fixed Position (Immune to Scrolling) */}
      <header className="fixed top-4 inset-x-0 z-40 mx-auto hidden w-full max-w-4xl px-4 sm:block pointer-events-none">
        <div className="glass-capsule pointer-events-auto flex items-center justify-between gap-3 rounded-full px-5 py-2.5 shadow-floating transition-colors duration-200">
          {/* Brand Wordmark & Logo */}
          <Link
            to="/"
            className="focus-ring flex items-center gap-2.5 rounded-full pr-2 transition hover:opacity-90"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-full glass-card p-1 shadow-2xs">
              <img src={kiwiIcon} alt="Kiwi" className="h-7 w-7 object-contain" />
            </div>
            <span className="font-display text-base font-extrabold text-stone-900 dark:text-white tracking-tight">
              Kiwi
            </span>
          </Link>

          {/* Nav Links + Theme Switcher */}
          <nav className="flex items-center gap-1.5" aria-label="Primary Desktop Navigation">
            <div ref={navContainerRef} className="relative flex items-center gap-1 sm:gap-1.5">
              {/* Dynamic Sliding Active Indicator Pill */}
              <div
                className={`absolute rounded-full bg-stone-900 dark:bg-stone-100 shadow-xs pointer-events-none ${
                  isReady ? 'transition-all duration-300 ease-[cubic-bezier(0.2,0.8,0.2,1)]' : ''
                }`}
                style={{
                  transform: `translate3d(${pillStyle.left}px, ${pillStyle.top}px, 0)`,
                  width: `${pillStyle.width}px`,
                  height: `${pillStyle.height}px`,
                  opacity: pillStyle.opacity,
                  willChange: 'transform, width',
                }}
                aria-hidden="true"
              />

              {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  ref={(el) => {
                    itemRefs.current[to] = el
                  }}
                  className={({ isActive }) =>
                    `relative z-10 focus-ring flex items-center gap-1.5 sm:gap-2 rounded-full px-2.5 sm:px-3.5 py-1.5 sm:py-2 text-xs md:text-sm font-semibold transition-colors duration-200 ${
                      isActive
                        ? 'text-white dark:text-stone-900'
                        : 'text-stone-600 dark:text-stone-300 hover:text-stone-900 dark:hover:text-white'
                    }`
                  }
                >
                  <Icon className="h-4 w-4" />
                  <span>{label}</span>
                </NavLink>
              ))}
            </div>

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
                <Moon className="h-4.5 w-4.5 text-kiwi-flesh transition-transform duration-200 hover:-rotate-12" />
              )}
            </button>
          </nav>
        </div>
      </header>

      {/* Mobile Top Header Bar - Fixed Position (Immune to Scrolling) */}
      <header className="fixed top-0 inset-x-0 z-40 flex items-center justify-between glass-panel px-5 py-3 transition-colors duration-200 sm:hidden">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-full glass-card p-0.5 shadow-2xs">
            <img src={kiwiIcon} alt="Kiwi" className="h-6 w-6 object-contain" />
          </div>
          <span className="font-display text-base font-extrabold text-stone-900 dark:text-white">Kiwi</span>
        </Link>
        <div className="flex items-center gap-2">
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

      {/* Mobile Floating Bottom Dock - Translucent Crystal Glass */}
      <nav
        className="fixed bottom-3 inset-x-3 z-50 flex justify-around rounded-2xl glass-capsule py-2 px-1 shadow-lift transition-colors duration-200 sm:hidden"
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
