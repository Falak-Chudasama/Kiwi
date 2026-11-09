import { describe, it, expect, vi, beforeEach } from 'vitest'
import { downloadUrl, pollJob, type JobStatus } from '../lib/api'

describe('client api', () => {
  it('generates correct download url', () => {
    expect(downloadUrl('job-123', 0)).toBe('/api/jobs/job-123/download/0')
    expect(downloadUrl('job-abc', 2)).toBe('/api/jobs/job-abc/download/2')
  })

  it('aborts polling immediately when AbortSignal fires', async () => {
    const controller = new AbortController()
    controller.abort()

    await expect(
      pollJob('job-test', { signal: controller.signal }),
    ).rejects.toThrow('Operation aborted by user.')
  })
})

