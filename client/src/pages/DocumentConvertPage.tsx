import { useEffect, useMemo, useState } from 'react'
import { AlertCircle, ArrowRightLeft, CheckCircle2 } from 'lucide-react'
import { PageShell } from '../components/layout/PageShell'
import { Dropzone } from '../components/features/Dropzone'
import { FileChip, formatBytes } from '../components/features/FileChip'
import { FormatPicker, type FormatOption } from '../components/features/FormatPicker'
import { ProgressPanel } from '../components/features/ProgressPanel'
import { ResultPanel } from '../components/features/ResultPanel'
import { useJobRunner } from '../hooks/useJobRunner'
import { fetchTargets } from '../lib/api'
import { useToast } from '../components/ui/ToastProvider'
import { categoryOf } from '../components/features/formatUtils'

export default function DocumentConvertPage() {
  const [file, setFile] = useState<File | null>(null)
  const [targets, setTargets] = useState<FormatOption[]>([])
  const [targetExt, setTargetExt] = useState<string | null>(null)
  const { state, progress, jobId, results, kind, errorMessage, run, reset } = useJobRunner()
  const toast = useToast()

  useEffect(() => {
    let cancelled = false
    if (!file) {
      setTargets([])
      setTargetExt(null)
      return
    }

    fetchTargets('documents', file.name).then((options) => {
      if (cancelled) return
      setTargets(options)
      setTargetExt(options.find((o) => o.supported)?.ext ?? null)
    }).catch(() => {
      if (!cancelled) toast.push('error', 'Could not determine conversion targets.')
    })

    return () => { cancelled = true }
  }, [file, toast])

  const sourceCategory = useMemo(() => categoryOf(file?.name ?? ''), [file])
  const supportedCount = targets.filter((o) => o.supported).length

  const handleConvert = async () => {
    if (!file || !targetExt) return
    const formData = new FormData()
    formData.append('file', file)
    formData.append('target_ext', targetExt)
    await run('/api/documents/convert', formData)
  }

  const isBusy = state === 'uploading' || state === 'processing'

  return (
    <PageShell title="Convert any file" description="Choose an output format. Kiwi enables the formats it can produce reliably on this machine." icon={<ArrowRightLeft className="h-5 w-5" />}>
      {!file ? (
        <Dropzone onFiles={(files) => { reset(); setFile(files[0]) }} hint="PDF, Office, text, image, audio, video, archive, and more" />
      ) : (
        <div className="space-y-5">
          <FileChip
            name={file.name}
            sizeLabel={`${formatBytes(file.size)} · ${sourceCategory}`}
            onRemove={state === 'idle' ? () => { reset(); setFile(null) } : undefined}
          />

          {state === 'idle' && targets.length ? (
            <div className="rounded-[1.5rem] border border-stone-200 bg-white p-5 shadow-sm">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-bold text-kiwi-ink">Output format</p>
                  <p className="mt-1 text-xs text-kiwi-ink/45">Unavailable formats are disabled.</p>
                </div>
                <span className="rounded-full bg-kiwi-flesh-50 px-2.5 py-1 text-xs font-bold text-kiwi-flesh-700">{supportedCount} available</span>
              </div>
              <FormatPicker options={targets} value={targetExt} onChange={setTargetExt} />
            </div>
          ) : null}

          {state === 'idle' && !targetExt ? (
            <div className="flex items-start gap-2 rounded-2xl border border-amber-100 bg-amber-50 px-4 py-3 text-sm text-amber-700">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              No supported output is available for this file with the installed conversion engines.
            </div>
          ) : null}

          {state === 'idle' && targetExt ? (
            <div className="flex items-center gap-2 rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-kiwi-ink/55">
              <CheckCircle2 className="h-4 w-4 text-kiwi-flesh-700" />
              <span className="truncate">{file.name}</span>
              <span>→</span>
              <strong className="text-kiwi-flesh-700">{targetExt.toUpperCase()}</strong>
            </div>
          ) : null}

          {state === 'idle' ? (
            <button type="button" onClick={handleConvert} disabled={!targetExt} className="focus-ring w-full rounded-2xl bg-kiwi-flesh px-5 py-3.5 text-sm font-bold text-white transition hover:bg-kiwi-flesh-600 disabled:cursor-not-allowed disabled:opacity-45">
              Convert
            </button>
          ) : null}

          {isBusy ? <ProgressPanel label="Converting…" progress={progress} /> : null}
          {state === 'done' && jobId ? <ResultPanel jobId={jobId} results={results} kind={kind ?? 'document_convert'} originalSize={file.size} onReset={() => { reset(); setFile(null) }} /> : null}
          {state === 'failed' ? <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-600">{errorMessage}</div> : null}
        </div>
      )}
    </PageShell>
  )
}
