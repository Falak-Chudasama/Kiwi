import { useCallback, useEffect, useRef, useState } from 'react'
import {
  cancelJob,
  pollJob,
  submitForm,
  type JobResultFile,
  type JobStatus,
  type JobStatusType,
} from '../lib/api'

export type RunState =
  | 'idle'
  | 'uploading'
  | 'queued'
  | 'processing'
  | 'finalizing'
  | 'done'
  | 'failed'
  | 'cancelled'

export interface UseJobRunnerResult {
  state: RunState
  progress: number
  jobId: string | null
  results: JobResultFile[]
  kind: string | null
  errorMessage: string | null
  isBusy: boolean
  run: (url: string, formData: FormData) => Promise<void>
  cancel: () => Promise<void>
  reset: () => void
}

export function useJobRunner(): UseJobRunnerResult {
  const [state, setState] = useState<RunState>('idle')
  const [progress, setProgress] = useState(0)
  const [jobId, setJobId] = useState<string | null>(null)
  const [results, setResults] = useState<JobResultFile[]>([])
  const [kind, setKind] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const abortControllerRef = useRef<AbortController | null>(null)
  const activeJobIdRef = useRef<string | null>(null)
  const isMountedRef = useRef(true)

  useEffect(() => {
    isMountedRef.current = true
    return () => {
      isMountedRef.current = false
      abortControllerRef.current?.abort()
    }
  }, [])

  const cancel = useCallback(async () => {
    const currentJobId = activeJobIdRef.current
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }

    if (currentJobId) {
      try {
        await cancelJob(currentJobId)
      } catch {
        // Best effort cancellation notice
      }
    }

    if (isMountedRef.current) {
      setState('cancelled')
      setErrorMessage('Operation cancelled.')
    }
  }, [])

  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    activeJobIdRef.current = null
    if (isMountedRef.current) {
      setState('idle')
      setProgress(0)
      setJobId(null)
      setResults([])
      setKind(null)
      setErrorMessage(null)
    }
  }, [])

  const run = useCallback(async (url: string, formData: FormData) => {
    // Synchronous guard against double submit
    if (
      state === 'uploading' ||
      state === 'queued' ||
      state === 'processing' ||
      state === 'finalizing'
    ) {
      return
    }

    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    const controller = new AbortController()
    abortControllerRef.current = controller

    setState('uploading')
    setErrorMessage(null)
    setProgress(5)
    setResults([])

    try {
      const { job_id } = await submitForm(url, formData, controller.signal)
      if (controller.signal.aborted || !isMountedRef.current) return

      activeJobIdRef.current = job_id
      setJobId(job_id)
      setState('queued')
      setProgress(15)

      const finalStatus: JobStatus = await pollJob(job_id, {
        signal: controller.signal,
        onUpdate: (status) => {
          if (!isMountedRef.current || controller.signal.aborted) return
          if (activeJobIdRef.current !== job_id) return // discard stale callback

          setProgress(status.progress)
          setKind(status.kind)
          if (status.status === 'processing') setState('processing')
          else if (status.status === 'finalizing') setState('finalizing')
        },
      })

      if (!isMountedRef.current || controller.signal.aborted) return
      if (activeJobIdRef.current !== job_id) return

      setResults(finalStatus.result_files)
      setKind(finalStatus.kind)
      setProgress(100)
      setState('done')
    } catch (err: unknown) {
      if (controller.signal.aborted || !isMountedRef.current) {
        setState('cancelled')
        return
      }
      const message = err instanceof Error ? err.message : 'Something went wrong.'
      setErrorMessage(message)
      setState('failed')
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null
      }
    }
  }, [state])

  const isBusy =
    state === 'uploading' ||
    state === 'queued' ||
    state === 'processing' ||
    state === 'finalizing'

  return {
    state,
    progress,
    jobId,
    results,
    kind,
    errorMessage,
    isBusy,
    run,
    cancel,
    reset,
  }
}
