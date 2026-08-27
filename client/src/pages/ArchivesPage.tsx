import { useState } from 'react'
import { PageShell } from '../components/layout/PageShell'
import { Dropzone } from '../components/features/Dropzone'
import { FileChip, formatBytes } from '../components/features/FileChip'
import { ProgressPanel } from '../components/features/ProgressPanel'
import { ResultPanel } from '../components/features/ResultPanel'
import { ArchiveIcon } from '../components/ui/icons'
import { useJobRunner } from '../hooks/useJobRunner'

type Mode = 'create' | 'extract'

const ARCHIVE_FORMATS = ['zip', '7z', 'tar']
const ARCHIVE_EXTENSIONS = new Set(['zip', '7z', 'tar', 'gz', 'bz2', 'xz', 'rar'])

export default function ArchivesPage() {
  const [mode, setMode] = useState<Mode>('create')
  const [files, setFiles] = useState<File[]>([])
  const [archiveFormat, setArchiveFormat] = useState('zip')
  const { state, progress, jobId, fileCount, errorMessage, run, reset } = useJobRunner()

  const switchMode = (next: Mode) => {
    setMode(next)
    reset()
    setFiles([])
  }

  const handleFiles = (incoming: File[]) => {
    reset()
    setFiles(incoming)
  }

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleRun = async () => {
    if (!files.length) return
    const formData = new FormData()

    if (mode === 'create') {
      files.forEach((f) => formData.append('files', f))
      formData.append('archive_format', archiveFormat)
      formData.append('name', 'kiwi-archive')
      await run('/api/archives/create', formData)
    } else {
      formData.append('file', files[0])
      await run('/api/archives/extract', formData)
    }
  }

  const isBusy = state === 'uploading' || state === 'processing'

  return (
    <PageShell
      title="Archives"
      description="Bundle files into a zip, 7z, or tar — or unpack one you already have."
      icon={<ArchiveIcon className="h-5 w-5" />}
    >
      <div className="mb-6 inline-flex rounded-2xl border border-kiwi-shell-50 bg-white p-1.5">
        {(['create', 'extract'] as Mode[]).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => switchMode(m)}
            className={`rounded-xl px-4 py-2 text-sm font-semibold capitalize transition ${
              mode === m ? 'bg-kiwi-flesh text-white' : 'text-kiwi-ink/55 hover:text-kiwi-ink'
            }`}
          >
            {m}
          </button>
        ))}
      </div>

      {!files.length ? (
        <Dropzone
          onFiles={handleFiles}
          multiple={mode === 'create'}
          hint={
            mode === 'create'
              ? 'Drop any files to bundle together'
              : 'Drop a .zip, .7z, .tar, or .rar file'
          }
          accept={mode === 'extract' ? '.zip,.7z,.tar,.gz,.bz2,.xz,.rar' : undefined}
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

          {mode === 'create' && state === 'idle' ? (
            <div>
              <p className="mb-2.5 text-sm font-medium text-kiwi-ink/70">Archive format</p>
              <div className="flex gap-2">
                {ARCHIVE_FORMATS.map((fmt) => (
                  <button
                    key={fmt}
                    type="button"
                    onClick={() => setArchiveFormat(fmt)}
                    className={`focus-ring rounded-xl border px-4 py-2 text-sm font-semibold uppercase transition ${
                      archiveFormat === fmt
                        ? 'border-kiwi-flesh bg-kiwi-flesh text-white'
                        : 'border-kiwi-shell-50 bg-white text-kiwi-ink/70 hover:border-kiwi-flesh/40'
                    }`}
                  >
                    {fmt}
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {state === 'idle' ? (
            <button
              type="button"
              onClick={handleRun}
              className="focus-ring w-full rounded-xl bg-kiwi-flesh px-5 py-3 text-sm font-semibold text-white transition hover:bg-kiwi-flesh-600"
            >
              {mode === 'create' ? 'Create archive' : 'Extract archive'}
            </button>
          ) : null}

          {isBusy ? (
            <ProgressPanel
              label={mode === 'create' ? 'Building archive…' : 'Extracting archive…'}
              progress={progress}
            />
          ) : null}

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
