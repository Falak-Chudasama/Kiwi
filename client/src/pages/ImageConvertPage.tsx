import { useEffect, useState } from 'react'
import { PageShell } from '../components/layout/PageShell'
import { Dropzone } from '../components/features/Dropzone'
import { FileChip, formatBytes } from '../components/features/FileChip'
import { FormatPicker } from '../components/features/FormatPicker'
import { ProgressPanel } from '../components/features/ProgressPanel'
import { ResultPanel } from '../components/features/ResultPanel'
import { ImageStackIcon } from '../components/ui/icons'
import { useJobRunner } from '../hooks/useJobRunner'
import { fetchTargets } from '../lib/api'
import { useToast } from '../components/ui/ToastProvider'

export default function ImageConvertPage() {
  const [files, setFiles] = useState<File[]>([])
  const [targets, setTargets] = useState<string[]>([])
  const [targetExt, setTargetExt] = useState<string | null>(null)
  const { state, progress, jobId, fileCount, errorMessage, run, reset } = useJobRunner()
  const toast = useToast()

  useEffect(() => {
    if (!files.length) return
    fetchTargets('images', files[0].name)
      .then((options) => {
        setTargets(options)
        setTargetExt(options[0] ?? null)
      })
      .catch(() => toast.push('error', 'Could not read that image type.'))
  }, [files])

  const handleFiles = (incoming: File[]) => {
    reset()
    setFiles(incoming)
  }

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleConvert = async () => {
    if (!files.length || !targetExt) return
    const formData = new FormData()
    files.forEach((f) => formData.append('files', f))
    formData.append('target_ext', targetExt)
    await run('/api/images/convert', formData)
  }

  const isBusy = state === 'uploading' || state === 'processing'

  return (
    <PageShell
      title="Image Conversion"
      description="jpg, png, webp, avif, heic, svg, ico, tiff, gif, bmp — any to any."
      icon={<ImageStackIcon className="h-5 w-5" />}
    >
      {!files.length ? (
        <Dropzone
          onFiles={handleFiles}
          multiple
          hint="Drop one or several images — batch conversion is supported"
        />
      ) : (
        <div className="space-y-5">
          <div className="space-y-2">
            {files.map((file, index) => (
              <FileChip
                key={`${file.name}-${index}`}
                name={file.name}
                sizeLabel={formatBytes(file.size)}
                onRemove={state === 'idle' ? () => removeFile(index) : undefined}
              />
            ))}
          </div>

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
              Convert {files.length > 1 ? `${files.length} images` : 'image'}
            </button>
          ) : null}

          {isBusy ? <ProgressPanel label="Converting images…" progress={progress} /> : null}

          {state === 'done' && jobId ? (
            <ResultPanel
              jobId={jobId}
              fileCount={fileCount}
              onReset={() => {
                reset()
                setFiles([])
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
