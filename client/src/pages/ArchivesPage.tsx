import { useState } from 'react'
import {
  AlertCircle,
  Archive,
  FolderArchive,
  FolderOpen,
  PackageOpen,
} from 'lucide-react'
import { PageShell } from '../components/layout/PageShell'
import { Dropzone } from '../components/features/Dropzone'
import { FileChip, formatBytes } from '../components/features/FileChip'
import { ProgressPanel } from '../components/features/ProgressPanel'
import { ResultPanel } from '../components/features/ResultPanel'
import { TextField } from '../components/ui/TextField'
import { useJobRunner } from '../hooks/useJobRunner'

type ArchiveMode = 'create' | 'extract'

const ACCEPT_ARCHIVES = '.zip,.7z,.tar,.tar.gz,.tgz,.tar.bz2,.tbz2,.tar.xz,.txz,.rar'

export default function ArchivesPage() {
  const [mode, setMode] = useState<ArchiveMode>('create')
  const [files, setFiles] = useState<File[]>([])
  const [archiveFormat, setArchiveFormat] = useState('zip')
  const [archiveName, setArchiveName] = useState('')

  const { state, progress, jobId, results, kind, errorMessage, isBusy, run, cancel, reset } =
    useJobRunner()

  const switchMode = (nextMode: ArchiveMode) => {
    setMode(nextMode)
    reset()
    setFiles([])
    setArchiveName('')
  }

  const handleFiles = (incoming: File[]) => {
    reset()
    setFiles(incoming)
    if (mode === 'create' && incoming.length && !archiveName) {
      const stem = incoming[0].name.replace(/\.[^.]+$/, '')
      setArchiveName(incoming.length === 1 ? stem : 'bundle')
    }
  }

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
    reset()
  }

  const handleRun = async () => {
    if (!files.length) return
    const formData = new FormData()

    if (mode === 'create') {
      files.forEach((f) => formData.append('files', f))
      formData.append('archive_format', archiveFormat)
      formData.append('name', archiveName.trim() || 'bundle')
      await run('/api/archives/create', formData)
    } else {
      formData.append('file', files[0])
      await run('/api/archives/extract', formData)
    }
  }

  return (
    <PageShell
      title="Archive Workspace"
      description="Bundle files into compressed archives or safely unpack ZIP, 7Z, TAR, and RAR files."
      icon={<Archive className="h-4 w-4" />}
    >
      {/* Mode Switcher */}
      <div className="glass-panel flex gap-2 rounded-2xl p-2 shadow-soft">
        <button
          type="button"
          onClick={() => switchMode('create')}
          className={`flex-1 flex items-center justify-center gap-2.5 rounded-xl py-3 text-sm font-bold transition ${
            mode === 'create'
              ? 'bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-xs'
              : 'text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 hover:text-stone-900 dark:hover:text-white'
          }`}
        >
          <FolderArchive className="h-4 w-4" />
          <span>Create Archive</span>
        </button>
        <button
          type="button"
          onClick={() => switchMode('extract')}
          className={`flex-1 flex items-center justify-center gap-2.5 rounded-xl py-3 text-sm font-bold transition ${
            mode === 'extract'
              ? 'bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-xs'
              : 'text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 hover:text-stone-900 dark:hover:text-white'
          }`}
        >
          <PackageOpen className="h-4 w-4" />
          <span>Extract Archive</span>
        </button>
      </div>

      {!files.length ? (
        <Dropzone
          onFiles={handleFiles}
          multiple={mode === 'create'}
          accept={mode === 'extract' ? ACCEPT_ARCHIVES : undefined}
          hint={
            mode === 'create'
              ? 'Drop any files to bundle into an archive'
              : 'ZIP, 7Z, TAR, TAR.GZ, TAR.BZ2, TAR.XZ, or RAR'
          }
        />
      ) : (
        <div className="space-y-6">
          {/* Selected File(s) */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold uppercase tracking-wider text-stone-500 dark:text-stone-400">
                {mode === 'create' ? `Files to Bundle (${files.length})` : 'Target Archive'}
              </span>
              {state === 'idle' && (
                <button
                  type="button"
                  onClick={() => {
                    reset()
                    setFiles([])
                  }}
                  className="text-sm font-semibold text-stone-400 dark:text-stone-500 hover:text-stone-700 dark:hover:text-stone-300 transition"
                >
                  Clear all
                </button>
              )}
            </div>
            {files.map((file, idx) => (
              <FileChip
                key={`${file.name}-${idx}`}
                name={file.name}
                sizeLabel={formatBytes(file.size)}
                onRemove={state === 'idle' ? () => removeFile(idx) : undefined}
              />
            ))}
          </div>

          {/* Creation Options */}
          {mode === 'create' && state === 'idle' && (
            <div className="glass-panel rounded-2xl p-6 shadow-soft space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-stone-500 dark:text-stone-400">
                Archive Format & Naming
              </h2>

              <div className="flex gap-2.5">
                {['zip', '7z', 'tar'].map((fmt) => (
                  <button
                    key={fmt}
                    type="button"
                    onClick={() => setArchiveFormat(fmt)}
                    className={`flex-1 rounded-xl border py-3 text-sm font-extrabold uppercase transition ${
                      archiveFormat === fmt
                        ? 'border-kiwi-flesh bg-kiwi-flesh text-white shadow-soft ring-2 ring-kiwi-flesh/20 dark:border-kiwi-lime dark:bg-kiwi-flesh dark:ring-kiwi-lime/30'
                        : 'border-stone-200/90 dark:border-white/[0.08] bg-white dark:bg-[#1C1D18] text-stone-700 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-[#22231E] shadow-2xs'
                    }`}
                  >
                    .{fmt}
                  </button>
                ))}
              </div>

              <div>
                <label className="block text-sm font-bold text-stone-700 dark:text-stone-300 mb-1.5">
                  Archive Bundle Name
                </label>
                <TextField
                  placeholder="e.g. project-archive"
                  value={archiveName}
                  onChange={(e) => setArchiveName(e.target.value)}
                />
              </div>
            </div>
          )}

          {/* Action Trigger */}
          {state === 'idle' && (
            <div className="flex justify-end">
              <button
                type="button"
                onClick={handleRun}
                disabled={isBusy}
                className="btn-glass-primary w-full sm:w-auto"
              >
                <span>{mode === 'create' ? 'Create Archive Package' : 'Extract Archive Contents'}</span>
              </button>
            </div>
          )}

          {/* Progress */}
          {isBusy && (
            <ProgressPanel
              label={mode === 'create' ? 'Compressing entries into bundle…' : 'Extracting entries with traversal checks…'}
              progress={progress}
              onCancel={cancel}
            />
          )}

          {/* Results */}
          {state === 'done' && jobId && (
            <ResultPanel
              jobId={jobId}
              results={results}
              kind={kind ?? (mode === 'extract' ? 'archive_extract' : 'archive_create')}
              originalSize={files.length === 1 ? files[0].size : undefined}
              onReset={() => {
                reset()
                setFiles([])
              }}
            />
          )}

          {/* Error Message */}
          {state === 'failed' && (
            <div className="flex items-start gap-3 rounded-2xl border border-rose-100 dark:border-rose-900/50 bg-rose-50/80 dark:bg-rose-950/40 p-4 text-xs text-rose-700 dark:text-rose-300 animate-slide-up">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-semibold">Archive operation failed</p>
                <p className="mt-1 text-rose-600 dark:text-rose-400">{errorMessage}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </PageShell>
  )
}
