import { describe, it, expect, vi, beforeEach } from 'vitest'
import { detectDocument, fetchScannerPresets, submitScannerJob } from '../lib/api'

describe('Scanner Client API', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('fetches scanner presets correctly', async () => {
    const mockPresets = [
      {
        id: 'auto',
        name: 'Auto',
        description: 'Auto preset',
        is_builtin: true,
        version: 1,
        settings: {
          filter_mode: 'color',
          brightness: 0,
          contrast: 10,
          exposure: 0,
          shadows: 0,
          highlights: 0,
          whites: 25,
          blacks: 15,
          gamma: 1,
          sharpen: 0.35,
          denoise: 0.2,
          remove_shadows: true,
          preserve_color_stamps: true,
          dewarp_enabled: false,
          ocr_enabled: true,
          ocr_language: 'eng',
        },
      },
    ]

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockPresets,
    } as any)

    const presets = await fetchScannerPresets()
    expect(presets).toHaveLength(1)
    expect(presets[0].id).toBe('auto')
    expect(globalThis.fetch).toHaveBeenCalledWith('/api/v1/scanner/presets', { signal: undefined })
  })

  it('submits scanner job with formData', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ job_id: 'scan-job-123' }),
    } as any)

    const fd = new FormData()
    fd.append('preset_id', 'receipt')
    const res = await submitScannerJob(fd)
    expect(res.job_id).toBe('scan-job-123')
  })
})

