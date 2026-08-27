export interface JobResponse {
  job_id: string
}

export interface JobStatus {
  id: string
  kind: string
  status: 'queued' | 'processing' | 'done' | 'failed'
  progress: number
  error: string | null
  result_files: string[]
}

async function parseOrThrow(res: Response) {
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.detail ?? `Request failed with status ${res.status}`)
  }
  return res.json()
}

export async function submitForm(url: string, formData: FormData): Promise<JobResponse> {
  const res = await fetch(url, { method: 'POST', body: formData })
  return parseOrThrow(res)
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const res = await fetch(`/api/jobs/${jobId}`)
  return parseOrThrow(res)
}

export function downloadUrl(jobId: string, fileIndex: number): string {
  return `/api/jobs/${jobId}/download/${fileIndex}`
}

export async function pollJob(
  jobId: string,
  onUpdate: (status: JobStatus) => void,
  intervalMs = 900,
): Promise<JobStatus> {
  return new Promise((resolve, reject) => {
    const tick = async () => {
      try {
        const status = await getJobStatus(jobId)
        onUpdate(status)
        if (status.status === 'done') {
          resolve(status)
          return
        }
        if (status.status === 'failed') {
          reject(new Error(status.error ?? 'Job failed.'))
          return
        }
        window.setTimeout(tick, intervalMs)
      } catch (err) {
        reject(err)
      }
    }
    tick()
  })
}

export async function fetchTargets(kind: 'documents' | 'images', filename: string): Promise<string[]> {
  const res = await fetch(`/api/${kind}/targets?filename=${encodeURIComponent(filename)}`)
  const data = await parseOrThrow(res)
  return data.targets
}
