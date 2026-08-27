import { useCallback, useState } from 'react'
import { pollJob, submitForm, type JobStatus } from '../lib/api'

type RunState = 'idle' | 'uploading' | 'processing' | 'done' | 'failed'

interface UseJobRunnerResult {
  state: RunState
  progress: number
  jobId: string | null
  fileCount: number
  errorMessage: string | null
  run: (url: string, formData: FormData) => Promise<void>
  reset: () => void
}

export function useJobRunner(): UseJobRunnerResult {
  const [state, setState] = useState<RunState>('idle')
  const [progress, setProgress] = useState(0)
  const [jobId, setJobId] = useState<string | null>(null)
  const [fileCount, setFileCount] = useState(0)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const run = useCallback(async (url: string, formData: FormData) => {
    setState('uploading')
    setErrorMessage(null)
    setProgress(0)

    try {
      const { job_id } = await submitForm(url, formData)
      setJobId(job_id)
      setState('processing')

      const finalStatus: JobStatus = await pollJob(job_id, (status) => {
        setProgress(status.progress)
      })

      setFileCount(finalStatus.result_files.length)
      setState('done')
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Something went wrong.')
      setState('failed')
    }
  }, [])

  const reset = useCallback(() => {
    setState('idle')
    setProgress(0)
    setJobId(null)
    setFileCount(0)
    setErrorMessage(null)
  }, [])

  return { state, progress, jobId, fileCount, errorMessage, run, reset }
}
