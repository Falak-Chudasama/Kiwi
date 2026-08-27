import { useCallback, useState } from 'react'
import { pollJob, submitForm, type JobResultFile, type JobStatus } from '../lib/api'

type RunState = 'idle' | 'uploading' | 'processing' | 'done' | 'failed'

interface UseJobRunnerResult {
  state: RunState
  progress: number
  jobId: string | null
  results: JobResultFile[]
  kind: string | null
  errorMessage: string | null
  run: (url: string, formData: FormData) => Promise<void>
  reset: () => void
}

export function useJobRunner(): UseJobRunnerResult {
  const [state, setState] = useState<RunState>('idle')
  const [progress, setProgress] = useState(0)
  const [jobId, setJobId] = useState<string | null>(null)
  const [results, setResults] = useState<JobResultFile[]>([])
  const [kind, setKind] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const run = useCallback(async (url: string, formData: FormData) => {
    setState('uploading'); setErrorMessage(null); setProgress(0); setResults([])
    try {
      const { job_id } = await submitForm(url, formData)
      setJobId(job_id)
      setState('processing')
      const finalStatus: JobStatus = await pollJob(job_id, (status) => {
        setProgress(status.progress)
        setKind(status.kind)
      })
      setResults(finalStatus.result_files)
      setKind(finalStatus.kind)
      setState('done')
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Something went wrong.')
      setState('failed')
    }
  }, [])

  const reset = useCallback(() => {
    setState('idle'); setProgress(0); setJobId(null); setResults([]); setKind(null); setErrorMessage(null)
  }, [])

  return { state, progress, jobId, results, kind, errorMessage, run, reset }
}
