import { useEffect, useState } from 'react'
import { PageShell } from '../components/layout/PageShell'
import { Dropzone } from '../components/features/Dropzone'
import { FileChip, formatBytes } from '../components/features/FileChip'
import { FormatPicker } from '../components/features/FormatPicker'
import { ProgressPanel } from '../components/features/ProgressPanel'
import { ResultPanel } from '../components/features/ResultPanel'
import { DocumentIcon } from '../components/ui/icons'
import { useJobRunner } from '../hooks/useJobRunner'
import { fetchTargets } from '../lib/api'
import { useToast } from '../components/ui/ToastProvider'

export default function DocumentConvertPage() {
  const [file, setFile] = useState<File | null>(null)
  const [targets, setTargets] = useState<string[]>([])
  const [targetExt, setTargetExt] = useState<string | null>(null)
  const { state, progress, jobId, fileCount, errorMessage, run, reset } = useJobRunner()
  const toast = useToast()

  useEffect(() => {
    if (!file) return
    fetchTargets('documents', file.name)
      .then((options) => {
        setTargets(options)
        setTargetExt(options[0] ?? null)
      })
      .catch(() => toast.push('error', 'Could not read that file type.'))
  }, [file])

  const handleFiles = (files: File[]) => {
    reset()
    setFile(files[0])
  }

  const handleConvert = async () => {
    if (!file || !targetExt) return
    const formData = new FormData()
    formData.append('file', file)
    formData.append('target_ext', targetExt)
    await run('/api/documents/convert', formData)
  }

  const isBusy = state === 'uploading' || state === 'processing'

  return (
    <PageShell
      title="Document Conversion"
      description="docx, pdf, odt, markdown, html, epub, and spreadsheets — all local."
      icon={<DocumentIcon className="h-5 w-5" />}
    >
      {!file ? (
        <Dropzone
          onFiles={handleFiles}
          hint="docx, pdf, odt, rtf, md, html, epub, xlsx, pptx, and more"
        />
      ) : (
        <div className="space-y-5">
          <FileChip
            name={file.name}
            sizeLabel={formatBytes(file.size)}
            onRemove={state === 'idle' ? () => setFile(null) : undefined}
          />

          {state === 'idle' && targets.length > 0 ? (
            <div>
              <p className="mb-2.5 text-sm font-medium text-kiwi-ink/70">Convert to</p>
              <FormatPicker options={targets} value={targetExt} onChange={setTargetExt} />
            </div>
          ) : null}

          {state === 'idle' ? (
            <button
              type="button"
              onClick={handleConvert}
              disabled={!targetExt}
              className="focus-ring w-full rounded-xl bg-kiwi-flesh px-5 py-3 text-sm font-semibold text-white transition hover:bg-kiwi-flesh-600 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Convert file
            </button>
          ) : null}

          {isBusy ? <ProgressPanel label="Converting document…" progress={progress} /> : null}

          {state === 'done' && jobId ? (
            <ResultPanel
              jobId={jobId}
              fileCount={fileCount}
              onReset={() => {
                reset()
                setFile(null)
              }}
            />
          ) : null}

          {state === 'failed' ? (
            <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-600">
              {errorMessage}
            </div>
          ) : null}
        </div>
      )}
    </PageShell>
  )
}
