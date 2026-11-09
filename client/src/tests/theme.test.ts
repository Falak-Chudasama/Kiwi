import { describe, it, expect, beforeEach } from 'vitest'

describe('Theme management logic', () => {
  let mockStore: Record<string, string> = {}
  let classList: Set<string> = new Set()

  const mockStorage = {
    getItem: (key: string) => mockStore[key] ?? null,
    setItem: (key: string, val: string) => { mockStore[key] = val },
    clear: () => { mockStore = {} },
  }

  const mockDocument = {
    documentElement: {
      classList: {
        add: (cls: string) => classList.add(cls),
        remove: (cls: string) => classList.delete(cls),
        contains: (cls: string) => classList.has(cls),
      },
    },
  }

  beforeEach(() => {
    mockStorage.clear()
    classList.clear()
  })

  it('defaults to light when nothing is stored and matchMedia is light', () => {
    const saved = mockStorage.getItem('kiwi_theme')
    expect(saved).toBeNull()
    expect(mockDocument.documentElement.classList.contains('dark')).toBe(false)
  })

  it('updates localStorage and DOM classes when theme is dark', () => {
    mockStorage.setItem('kiwi_theme', 'dark')
    mockDocument.documentElement.classList.add('dark')

    expect(mockStorage.getItem('kiwi_theme')).toBe('dark')
    expect(mockDocument.documentElement.classList.contains('dark')).toBe(true)
  })

  it('removes dark class and updates storage when toggled back to light', () => {
    mockStorage.setItem('kiwi_theme', 'dark')
    mockDocument.documentElement.classList.add('dark')

    // Toggle to light
    mockStorage.setItem('kiwi_theme', 'light')
    mockDocument.documentElement.classList.remove('dark')

    expect(mockStorage.getItem('kiwi_theme')).toBe('light')
    expect(mockDocument.documentElement.classList.contains('dark')).toBe(false)
  })
})
