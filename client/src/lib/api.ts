export interface JobResponse { job_id: string }

export interface JobResultFile {
  name: string
  size: number
  media_type: string
}

export interface JobStatus {
  id: string
  kind: string
  status: 'queued' | 'processing' | 'done' | 'failed'
  progress: number
  error: string | null
  result_files: JobResultFile[]
}

async function parseOrThrow(res: Response) {
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.detail ?? `Request failed with status ${res.status}`)
  }
  return res.json()
}

export async function submitForm(url: string, formData: FormData): Promise<JobResponse> {
  return parseOrThrow(await fetch(url, { method: 'POST', body: formData }))
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  return parseOrThrow(await fetch(`/api/jobs/${jobId}`))
}

export function downloadUrl(jobId: string, fileIndex: number): string {
  return `/api/jobs/${jobId}/download/${fileIndex}`
}

export async function pollJob(jobId: string, onUpdate: (status: JobStatus) => void, intervalMs = 700): Promise<JobStatus> {
  return new Promise((resolve, reject) => {
    const tick = async () => {
      try {
        const status = await getJobStatus(jobId)
        onUpdate(status)
        if (status.status === 'done') return resolve(status)
        if (status.status === 'failed') return reject(new Error(status.error ?? 'Job failed.'))
        window.setTimeout(tick, intervalMs)
      } catch (err) { reject(err) }
    }
    tick()
  })
}

export interface TargetOption {
  ext: string
  category: string
  supported: boolean
  ready?: boolean
  reason?: string | null
}

export async function fetchTargets(kind: 'documents' | 'images', filename: string): Promise<TargetOption[]> {
  const res = await fetch(`/api/${kind}/targets?filename=${encodeURIComponent(filename)}`)
  const data = await parseOrThrow(res)
  return data.targets
}
