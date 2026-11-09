import { describe, it, expect } from 'vitest'
import { categoryOf, extensionOf, formatLabel } from '../components/features/formatUtils'
import { formatBytes } from '../components/features/FileChip'
import { cn } from '../lib/utils'

describe('formatUtils', () => {
  it('correctly extracts extensions including compound archives', () => {
    expect(extensionOf('document.docx')).toBe('docx')
    expect(extensionOf('photo.JPEG')).toBe('jpeg')
    expect(extensionOf('archive.tar.gz')).toBe('tar.gz')
    expect(extensionOf('backup.tar.bz2')).toBe('tar.bz2')
    expect(extensionOf('code.py')).toBe('py')
    expect(extensionOf('noextension')).toBe('')
  })

  it('resolves correct categories', () => {
    expect(categoryOf('document.pdf')).toBe('pdf')
    expect(categoryOf('image.webp')).toBe('image')
    expect(categoryOf('doc.odt')).toBe('document')
    expect(categoryOf('sheet.xlsx')).toBe('spreadsheet')
    expect(categoryOf('slides.pptx')).toBe('presentation')
    expect(categoryOf('bundle.7z')).toBe('archive')
    expect(categoryOf('audio.flac')).toBe('audio')
    expect(categoryOf('video.mkv')).toBe('video')
  })

  it('formats labels neatly', () => {
    expect(formatLabel('jpeg')).toBe('JPG')
    expect(formatLabel('png')).toBe('PNG')
    expect(formatLabel('pdf')).toBe('PDF')
  })
})

describe('formatBytes helper', () => {
  it('formats byte numbers into human readable strings', () => {
    expect(formatBytes(500)).toBe('500 B')
    expect(formatBytes(1536)).toBe('1.5 KB')
    expect(formatBytes(1048576 * 2.5)).toBe('2.5 MB')
    expect(formatBytes(1073741824 * 1.25)).toBe('1.25 GB')
  })
})

describe('cn utility', () => {
  it('merges class strings while filtering falsy values', () => {
    expect(cn('base', false && 'hidden', undefined, 'active')).toBe('base active')
    expect(cn()).toBe('')
  })
})

