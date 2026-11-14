import { createContext, useContext, useEffect, useState, useMemo, type ReactNode } from 'react'

type Theme = 'light' | 'dark'

interface ThemeContextType {
  theme: Theme
  isDark: boolean
  toggleTheme: () => void
  setTheme: (theme: Theme) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

const STORAGE_KEY = 'kiwi_theme'
const MANUAL_KEY = 'kiwi_theme_manual'

/**
 * Returns 'dark' for evening/night (>= 19:00 / 7 PM or < 06:00 / 6 AM)
 * and 'light' for daytime (06:00 to 18:59).
 */
export function getTimeBasedTheme(): Theme {
  const hour = new Date().getHours()
  return (hour >= 19 || hour < 6) ? 'dark' : 'light'
}

function getInitialTheme(): Theme {
  if (typeof window === 'undefined') return 'light'

  // If a URL parameter ?theme=light or ?theme=dark is provided, respect it
  try {
    const params = new URLSearchParams(window.location.search)
    const urlTheme = params.get('theme')
    if (urlTheme === 'light' || urlTheme === 'dark') {
      return urlTheme
    }
  } catch {
    // fallback
  }

  // If user already explicitly manually chose a mode in this session, respect it
  try {
    const isManual = sessionStorage.getItem(MANUAL_KEY)
    if (isManual === 'true') {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved === 'light' || saved === 'dark') {
        return saved
      }
    }
  } catch {
    // fallback
  }

  // Otherwise, automatically detect current time of day on launch
  return getTimeBasedTheme()
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(getInitialTheme)

  useEffect(() => {
    const root = document.documentElement
    if (theme === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }

    try {
      localStorage.setItem(STORAGE_KEY, theme)
    } catch {
      // ignore storage quota errors
    }

    // Update browser theme-color meta tag
    const meta = document.querySelector('meta[name="theme-color"]')
    if (meta) {
      meta.setAttribute('content', theme === 'dark' ? '#121310' : '#F8F9F5')
    }
  }, [theme])

  // Periodic automatic day/night time check (every 60s) if user hasn't manually overridden
  useEffect(() => {
    const interval = setInterval(() => {
      try {
        const isManual = sessionStorage.getItem(MANUAL_KEY)
        if (isManual !== 'true') {
          const autoTheme = getTimeBasedTheme()
          setThemeState((current) => (current !== autoTheme ? autoTheme : current))
        }
      } catch {
        // ignore
      }
    }, 60000)

    return () => clearInterval(interval)
  }, [])

  // Listen to OS theme changes if user hasn't manually set one yet
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = (e: MediaQueryListEvent) => {
      try {
        const isManual = sessionStorage.getItem(MANUAL_KEY)
        if (isManual !== 'true') {
          setThemeState(getTimeBasedTheme())
        }
      } catch {
        // ignore
      }
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  const toggleTheme = () => {
    try {
      sessionStorage.setItem(MANUAL_KEY, 'true')
    } catch {}
    setThemeState((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }

  const setTheme = (newTheme: Theme) => {
    try {
      sessionStorage.setItem(MANUAL_KEY, 'true')
    } catch {}
    setThemeState(newTheme)
  }

  const value = useMemo(
    () => ({
      theme,
      isDark: theme === 'dark',
      toggleTheme,
      setTheme,
    }),
    [theme]
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

