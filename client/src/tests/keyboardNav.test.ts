import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { normalizeNavPath, NAV_PAGES } from '../hooks/useKeyboardNav'

describe('Keyboard Navigation Hook Logic', () => {
  it('defines canonical nav pages in correct visual order', () => {
    expect(NAV_PAGES).toEqual([
      '/convert',
      '/scan',
      '/images',
      '/pdf',
      '/compress',
      '/archives',
    ])
  })

  it('normalizes legacy or alias routes', () => {
    expect(normalizeNavPath('/documents')).toBe('/convert')
    expect(normalizeNavPath('/scanner')).toBe('/scan')
    expect(normalizeNavPath('/convert')).toBe('/convert')
    expect(normalizeNavPath('/pdf')).toBe('/pdf')
    expect(normalizeNavPath('/')).toBe('/')
  })

  it('calculates forward and backward cycling indices correctly', () => {
    // Forward from convert (0) -> scan (1)
    const convertIdx = 0
    const nextAfterConvert = (convertIdx + 1) % NAV_PAGES.length
    expect(NAV_PAGES[nextAfterConvert]).toBe('/scan')

    // Forward wrap: archives (5) -> convert (0)
    const archivesIdx = 5
    const wrapForward = (archivesIdx + 1) % NAV_PAGES.length
    expect(NAV_PAGES[wrapForward]).toBe('/convert')

    // Backward from scan (1) -> convert (0)
    const scanIdx = 1
    const prevAfterScan = (scanIdx - 1 + NAV_PAGES.length) % NAV_PAGES.length
    expect(NAV_PAGES[prevAfterScan]).toBe('/convert')

    // Backward wrap: convert (0) -> archives (5)
    const wrapBackward = (convertIdx - 1 + NAV_PAGES.length) % NAV_PAGES.length
    expect(NAV_PAGES[wrapBackward]).toBe('/archives')
  })
})
