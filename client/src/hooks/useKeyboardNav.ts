import { useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { playScroll } from '../lib/sound'

export const NAV_PAGES = [
  '/convert',
  '/scan',
  '/images',
  '/pdf',
  '/compress',
  '/archives',
] as const

/**
 * Normalizes route pathnames to their canonical navbar item path.
 */
export function normalizeNavPath(pathname: string): string {
  if (pathname === '/documents') return '/convert'
  if (pathname === '/scanner') return '/scan'
  return pathname
}

/**
 * Global keyboard navigation hook.
 * Allows effortless cycling through navbar pages using:
 * - Ctrl + ArrowRight (any Ctrl key: Left Ctrl or Right Ctrl) -> next page
 * - Ctrl + ArrowLeft (any Ctrl key: Left Ctrl or Right Ctrl) -> previous page
 */
export function useKeyboardNav() {
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Must hold a Ctrl key (either Left Ctrl or Right Ctrl; e.ctrlKey detects any Ctrl key on all OSes).
      // Also allow e.metaKey for Mac command key convenience.
      if (!e.ctrlKey && !e.metaKey) return

      // Ignore if user is holding Shift or Alt (to avoid colliding with text selection/system commands)
      if (e.shiftKey || e.altKey) return

      // Don't intercept if user is actively editing text inside an input, textarea, or contentEditable
      const target = e.target as HTMLElement | null
      if (
        target &&
        (target.tagName === 'INPUT' ||
          target.tagName === 'TEXTAREA' ||
          target.isContentEditable)
      ) {
        return
      }

      const isRight = e.key === 'ArrowRight' || e.code === 'ArrowRight'
      const isLeft = e.key === 'ArrowLeft' || e.code === 'ArrowLeft'

      if (!isRight && !isLeft) return

      e.preventDefault()

      const currentPath = normalizeNavPath(location.pathname)
      const currentIndex = NAV_PAGES.indexOf(currentPath as any)

      let nextIndex = 0

      if (isRight) {
        if (currentIndex === -1) {
          // If starting from home or another route, enter at the first navbar page
          nextIndex = 0
        } else {
          // Cycle forward, wrapping around from Archives back to Convert
          nextIndex = (currentIndex + 1) % NAV_PAGES.length
        }
      } else if (isLeft) {
        if (currentIndex === -1) {
          // If starting from home or another route, enter at the last navbar page
          nextIndex = NAV_PAGES.length - 1
        } else {
          // Cycle backward, wrapping around from Convert back to Archives
          nextIndex = (currentIndex - 1 + NAV_PAGES.length) % NAV_PAGES.length
        }
      }

      const targetPath = NAV_PAGES[nextIndex]
      if (targetPath && targetPath !== location.pathname) {
        playScroll()
        navigate(targetPath)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [location.pathname, navigate])
}
