import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageShell } from '../components/layout/PageShell'
import { Dropzone } from '../components/features/Dropzone'
import { FileChip, formatBytes } from '../components/features/FileChip'
import { CompressionLevelSelector, type CompressionLevel } from '../components/features/CompressionLevelSelector'
import { ProgressPanel } from '../components/features/ProgressPanel'
import { ResultPanel } from '../components/features/ResultPanel'
import { CompressIcon } from '../components/ui/icons'
import { useJobRunner } from '../hooks/useJobRunner'
import { fetchSystemStatus } from '../lib/api'

export default function CompressPage() {
  const [file, setFile] = useState<File | null>(null)
  const [level, setLevel] = useState<CompressionLevel>('medium')
  const [ghostscriptInstalled, setGhostscriptInstalled] = useState<boolean | null>(null)
  const { state, progress, jobId, results, kind, errorMessage, run, reset } = useJobRunner()
  const handleFiles = (files: File[]) => { reset(); setFile(files[0]) }
  const handleCompress = async () => { if (!file) return; const formData = new FormData(); formData.append('file', file); formData.append('level', level); await run('/api/compress', formData) }
  const isBusy = state === 'uploading' || state === 'processing'
  const isPdf = file?.name.toLowerCase().endsWith('.pdf') ?? false

  useEffect(() => {
    if (!isPdf || ghostscriptInstalled !== null) return
    fetchSystemStatus()
      .then((data) => setGhostscriptInstalled(data.engines.find((e) => e.key === 'ghostscript')?.installed ?? true))
      .catch(() => setGhostscriptInstalled(true)) // fail open — don't nag if the check itself fails
  }, [isPdf, ghostscriptInstalled])

  return <PageShell title="Compression" description="Reduce PDFs and images by strength, with a hard no-larger-output fallback." icon={<CompressIcon className="h-5 w-5" />}>
    {!file ? <Dropzone onFiles={handleFiles} accept=".pdf,.jpg,.jpeg,.png,.webp,.tiff,.tif,.docx,.pptx,.xlsx" hint="PDF, JPG, PNG, WEBP, TIFF, DOCX, PPTX, XLSX" /> : <div className="space-y-5">
      <FileChip name={file.name} sizeLabel={formatBytes(file.size)} onRemove={state === 'idle' ? () => { reset(); setFile(null) } : undefined} />
      {isPdf && ghostscriptInstalled === false && state === 'idle' ? (
        <p className="rounded-xl border border-amber-100 bg-amber-50 px-4 py-3 text-sm text-amber-700">
          Ghostscript isn't installed, so PDF compression will fall back to page rasterization (slower, larger text can blur slightly).{' '}
          <Link to="/engines" className="font-bold underline underline-offset-2">Install it</Link> for better results.
        </p>
      ) : null}
      {state === 'idle' ? <div><p className="mb-2.5 text-sm font-bold text-kiwi-ink">Compression strength</p><CompressionLevelSelector value={level} onChange={setLevel} /></div> : null}
      {state === 'idle' ? <button type="button" onClick={handleCompress} className="focus-ring w-full rounded-2xl bg-kiwi-flesh px-5 py-3.5 text-sm font-bold text-white transition hover:bg-kiwi-flesh-600">Compress file</button> : null}
      {isBusy ? <ProgressPanel label="Compressing…" progress={progress} /> : null}
      {state === 'done' && jobId ? <ResultPanel jobId={jobId} results={results} kind={kind ?? 'compress_file'} originalSize={file.size} onReset={() => { reset(); setFile(null) }} /> : null}
      {state === 'failed' ? <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-600">{errorMessage}</div> : null}
    </div>}
  </PageShell>
}
