import { useState } from 'react'
import { PageShell } from '../components/layout/PageShell'
import { Dropzone } from '../components/features/Dropzone'
import { FileChip, formatBytes } from '../components/features/FileChip'
import { ProgressPanel } from '../components/features/ProgressPanel'
import { ResultPanel } from '../components/features/ResultPanel'
import { ArchiveIcon, PackageOpenIcon } from '../components/ui/icons'
import { useJobRunner } from '../hooks/useJobRunner'

type Mode = 'create' | 'extract'
const ACCEPT = '.zip,.7z,.tar,.tar.gz,.tgz,.tar.bz2,.tbz2,.tar.xz,.txz,.rar'

export default function ArchivesPage() {
  const [mode, setMode] = useState<Mode>('create')
  const [files, setFiles] = useState<File[]>([])
  const [archiveFormat, setArchiveFormat] = useState('zip')
  const { state, progress, jobId, results, kind, errorMessage, run, reset } = useJobRunner()

  const switchMode = (next: Mode) => { setMode(next); reset(); setFiles([]) }
  const handleFiles = (incoming: File[]) => { reset(); setFiles(incoming) }
  const removeFile = (index: number) => setFiles((prev) => prev.filter((_, i) => i !== index))
  const handleRun = async () => {
    if (!files.length) return
    const formData = new FormData()
    if (mode === 'create') {
      files.forEach((f) => formData.append('files', f))
      formData.append('archive_format', archiveFormat)
      const archiveName = files.length === 1 ? files[0].name.replace(/\.[^.]+$/, '') : 'bundle'
      formData.append('name', archiveName)
      await run('/api/archives/create', formData)
    } else {
      formData.append('file', files[0])
      await run('/api/archives/extract', formData)
    }
  }
  const isBusy = state === 'uploading' || state === 'processing'

  return <PageShell title="Archives" description="Create or extract supported archives." icon={<ArchiveIcon className="h-5 w-5" />}>
    <div className="mb-6 inline-flex rounded-2xl border border-stone-200 bg-white p-1.5 shadow-sm">
      {(['create', 'extract'] as Mode[]).map((m) => <button key={m} type="button" onClick={() => switchMode(m)} className={`rounded-xl px-4 py-2 text-sm font-bold transition ${mode === m ? 'bg-kiwi-flesh text-white' : 'text-kiwi-ink/50 hover:text-kiwi-ink'}`}>{m === 'create' ? 'Create archive' : 'Extract archive'}</button>)}
    </div>

    {!files.length ? <Dropzone onFiles={handleFiles} multiple={mode === 'create'} accept={mode === 'extract' ? ACCEPT : undefined} hint={mode === 'create' ? 'Drop any files to bundle together' : 'ZIP, 7Z, TAR, TAR.GZ, TAR.BZ2, TAR.XZ, or RAR'} /> : <div className="space-y-5">
      <div className="space-y-2">{files.map((file, index) => <FileChip key={`${file.name}-${index}`} name={file.name} sizeLabel={formatBytes(file.size)} onRemove={state === 'idle' ? () => removeFile(index) : undefined} />)}</div>
      {mode === 'create' && state === 'idle' ? <div className="rounded-3xl border border-stone-200 bg-white p-5"><p className="mb-3 text-sm font-bold text-kiwi-ink">Archive format</p><div className="flex gap-2">{['zip','7z','tar'].map((fmt) => <button key={fmt} type="button" onClick={() => setArchiveFormat(fmt)} className={`focus-ring rounded-xl border px-4 py-2.5 text-sm font-bold uppercase transition ${archiveFormat === fmt ? 'border-kiwi-flesh bg-kiwi-flesh text-white' : 'border-stone-200 bg-white text-kiwi-ink/60 hover:border-kiwi-flesh/40'}`}>{fmt}</button>)}</div></div> : null}
      {mode === 'extract' && state === 'idle' ? <div className="flex items-start gap-3 rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-kiwi-ink/55"><PackageOpenIcon className="mt-0.5 h-4 w-4 shrink-0" />Download each extracted file, or use Download all to start the individual downloads together.</div> : null}
      {state === 'idle' ? <button type="button" onClick={handleRun} className="focus-ring w-full rounded-2xl bg-kiwi-flesh px-5 py-3.5 text-sm font-bold text-white transition hover:bg-kiwi-flesh-600">{mode === 'create' ? `Create ${archiveFormat.toUpperCase()}` : 'Extract archive'}</button> : null}
      {isBusy ? <ProgressPanel label={mode === 'create' ? 'Creating archive…' : 'Extracting archive…'} progress={progress} /> : null}
      {state === 'done' && jobId ? <ResultPanel jobId={jobId} results={results} kind={kind ?? (mode === 'extract' ? 'archive_extract' : 'archive_create')} originalSize={files.length === 1 && mode === 'create' ? files[0].size : undefined} onReset={() => { reset(); setFiles([]) }} /> : null}
      {state === 'failed' ? <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-600">{errorMessage}</div> : null}
    </div>}
  </PageShell>
}
