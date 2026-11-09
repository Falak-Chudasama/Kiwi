export interface JobResponse {
  job_id: string
}

export interface JobResultFile {
  name: string
  size: number
  media_type: string
}

export type JobStatusType =
  | 'queued'
  | 'processing'
  | 'finalizing'
  | 'done'
  | 'failed'
  | 'cancelled'
  | 'expired'

export interface JobStatus {
  id: string
  kind: string
  status: JobStatusType
  progress: number
  error: string | null
  result_files: JobResultFile[]
  created_at?: number
  started_at?: number | null
  completed_at?: number | null
  expires_at?: number | null
}

async function parseOrThrow(res: Response) {
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.detail ?? `Request failed with status ${res.status}`)
  }
  return res.json()
}

export async function submitForm(
  url: string,
  formData: FormData,
  signal?: AbortSignal,
): Promise<JobResponse> {
  const res = await fetch(url, {
    method: 'POST',
    body: formData,
    signal,
  })
  return parseOrThrow(res)
}

export async function getJobStatus(
  jobId: string,
  signal?: AbortSignal,
): Promise<JobStatus> {
  const res = await fetch(`/api/jobs/${jobId}`, { signal })
  return parseOrThrow(res)
}

export async function cancelJob(jobId: string): Promise<{ cancelled: boolean }> {
  const res = await fetch(`/api/jobs/${jobId}/cancel`, { method: 'POST' })
  return parseOrThrow(res)
}

export function downloadUrl(jobId: string, fileIndex: number): string {
  return `/api/jobs/${jobId}/download/${fileIndex}`
}

export interface PollJobOptions {
  onUpdate?: (status: JobStatus) => void
  signal?: AbortSignal
  initialIntervalMs?: number
  maxIntervalMs?: number
  deadlineSeconds?: number
}

/**
 * Bounded, adaptive polling with cancellation, tab visibility awareness,
 * and transient error resilience.
 */
export async function pollJob(
  jobId: string,
  options: PollJobOptions = {},
): Promise<JobStatus> {
  const {
    onUpdate,
    signal,
    initialIntervalMs = 800,
    maxIntervalMs = 2500,
    deadlineSeconds = 600,
  } = options

  const startTime = Date.now()
  const maxEndTime = startTime + deadlineSeconds * 1000
  let currentInterval = initialIntervalMs
  let transientErrorCount = 0

  return new Promise((resolve, reject) => {
    let timeoutId: number | null = null

    const cleanup = () => {
      if (timeoutId !== null) {
        window.clearTimeout(timeoutId)
        timeoutId = null
      }
      signal?.removeEventListener('abort', onAbort)
    }

    const onAbort = () => {
      cleanup()
      reject(new DOMException('Operation aborted by user.', 'AbortError'))
    }

    if (signal?.aborted) {
      return onAbort()
    }
    signal?.addEventListener('abort', onAbort)

    const step = async () => {
      if (signal?.aborted) return

      if (Date.now() > maxEndTime) {
        cleanup()
        return reject(new Error('Job exceeded maximum polling deadline.'))
      }

      // If document is hidden (background tab), reduce polling frequency to save battery/network
      const effectiveInterval = document.hidden
        ? Math.max(currentInterval * 2, 3000)
        : currentInterval

      try {
        const status = await getJobStatus(jobId, signal)
        transientErrorCount = 0
        onUpdate?.(status)

        if (status.status === 'done') {
          cleanup()
          return resolve(status)
        }
        if (status.status === 'failed') {
          cleanup()
          return reject(new Error(status.error ?? 'Job failed.'))
        }
        if (status.status === 'cancelled') {
          cleanup()
          return reject(new Error('Job was cancelled.'))
        }
        if (status.status === 'expired') {
          cleanup()
          return reject(new Error('Job temporary workspace expired.'))
        }

        // Adaptive interval: gently back off up to maxIntervalMs
        currentInterval = Math.min(currentInterval + 150, maxIntervalMs)
        timeoutId = window.setTimeout(step, effectiveInterval)
      } catch (err) {
        if (signal?.aborted) return

        // Allow up to 3 transient network glitches before rejecting
        transientErrorCount += 1
        if (transientErrorCount >= 4) {
          cleanup()
          return reject(err)
        }
        timeoutId = window.setTimeout(step, currentInterval * 1.5)
      }
    }

    step()
  })
}

export interface TargetOption {
  ext: string
  category: string
  supported: boolean
  ready?: boolean
  status?: 'ready' | 'requires_engine' | 'degraded_or_lossy' | 'content_dependent' | 'unsupported'
  reason?: string | null
  strategy?: string | null
  fidelity?: string | null
}

export async function fetchTargets(
  kind: 'documents' | 'images',
  filename: string,
  signal?: AbortSignal,
): Promise<TargetOption[]> {
  const res = await fetch(`/api/${kind}/targets?filename=${encodeURIComponent(filename)}`, { signal })
  const data = await parseOrThrow(res)
  return data.targets
}

export interface EngineInstall {
  windows: string
  macos: string
  linux: string
}

export interface EngineStatus {
  key: string
  name: string
  unlocks: string
  install: EngineInstall
  installed: boolean
}

export interface SystemStatus {
  engines: EngineStatus[]
  missing_count: number
}

export async function fetchSystemStatus(signal?: AbortSignal): Promise<SystemStatus> {
  const res = await fetch('/api/system/status', { signal })
  return parseOrThrow(res)
}
