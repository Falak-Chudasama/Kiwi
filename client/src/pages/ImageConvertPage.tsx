import { useEffect, useState } from 'react'
import { PageShell } from '../components/layout/PageShell'
import { Dropzone } from '../components/features/Dropzone'
import { FileChip, formatBytes } from '../components/features/FileChip'
import { FormatPicker, type FormatOption } from '../components/features/FormatPicker'
import { ImagePreview } from '../components/features/ImagePreview'
import { ProgressPanel } from '../components/features/ProgressPanel'
import { ResultPanel } from '../components/features/ResultPanel'
import { ImageStackIcon } from '../components/ui/icons'
import { useJobRunner } from '../hooks/useJobRunner'
import { fetchTargets } from '../lib/api'
import { useToast } from '../components/ui/ToastProvider'

const IMAGE_ACCEPT = '.jpg,.jpeg,.png,.webp,.avif,.gif,.bmp,.tiff,.tif,.ico,.heic,.heif,.svg'

export default function ImageConvertPage() {
  const [files, setFiles] = useState<File[]>([])
  const [targets, setTargets] = useState<FormatOption[]>([])
  const [targetExt, setTargetExt] = useState<string | null>(null)
  const [width, setWidth] = useState('')
  const [height, setHeight] = useState('')
  const [exact, setExact] = useState(false)
  const { state, progress, jobId, results, kind, errorMessage, run, reset } = useJobRunner()
  const toast = useToast()

  useEffect(() => {
    if (!files.length) { setTargets([]); setTargetExt(null); return }
    fetchTargets('images', files[0].name).then((options) => {
      setTargets(options); setTargetExt(options.find((o) => o.supported)?.ext ?? null)
    }).catch(() => toast.push('error', 'Could not read that image type.'))
  }, [files, toast])

  const removeFile = (index: number) => setFiles((prev) => prev.filter((_, i) => i !== index))
  const handleFiles = (incoming: File[]) => { reset(); setFiles(incoming) }
  const handleConvert = async () => {
    if (!files.length || !targetExt) return
    const formData = new FormData(); files.forEach((f) => formData.append('files', f)); formData.append('target_ext', targetExt)
    if (width) formData.append('width', width)
    if (height) formData.append('height', height)
    formData.append('fit_mode', exact ? 'exact' : 'contain')
    await run('/api/images/convert', formData)
  }
  const isBusy = state === 'uploading' || state === 'processing'

  return (
    <PageShell title="Image Conversion" description="Convert, resize, preview, and batch-process common image formats." icon={<ImageStackIcon className="h-5 w-5" />}>
      {!files.length ? <Dropzone onFiles={handleFiles} multiple accept={IMAGE_ACCEPT} hint="Only image files are selectable here" /> : (
        <div className="space-y-5">
          <ImagePreview files={files} />
          <div className="space-y-2">{files.map((file, index) => <FileChip key={`${file.name}-${index}`} name={file.name} sizeLabel={formatBytes(file.size)} onRemove={state === 'idle' ? () => removeFile(index) : undefined} />)}</div>
          {state === 'idle' && targets.length ? <div className="rounded-3xl border border-stone-200 bg-white p-5"><div className="mb-3 flex items-center justify-between gap-3"><p className="text-sm font-bold text-kiwi-ink">Convert to</p><span className="text-xs text-kiwi-ink/40">Unavailable formats are disabled</span></div><FormatPicker options={targets} value={targetExt} onChange={setTargetExt} priorityGroup="Images" /></div> : null}
          {state === 'idle' ? <button type="button" onClick={handleConvert} disabled={!targetExt} className="focus-ring w-full rounded-2xl bg-kiwi-flesh px-5 py-3.5 text-sm font-bold text-white transition hover:bg-kiwi-flesh-600 disabled:cursor-not-allowed disabled:opacity-45">Convert {files.length > 1 ? `${files.length} images` : 'image'}</button> : null}
          {state === 'idle' ? <details className="group rounded-3xl border border-stone-200 bg-white p-5 open:pb-5"><summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-sm font-bold text-kiwi-ink"><span>Resize (optional)</span><span className="text-xs font-semibold text-kiwi-ink/40 transition group-open:rotate-180">▾</span></summary><div className="mt-4"><p className="text-xs text-kiwi-ink/45">Leave a field blank to keep the aspect ratio from the value you provide.</p><div className="mt-3 grid gap-3 sm:grid-cols-2"><label className="text-xs font-semibold text-kiwi-ink/55">Width (px)<input inputMode="numeric" type="number" min="1" value={width} onChange={(e) => setWidth(e.target.value)} placeholder="Auto" className="focus-ring mt-1.5 w-full rounded-xl border border-stone-200 bg-white px-3 py-2.5 text-sm" /></label><label className="text-xs font-semibold text-kiwi-ink/55">Height (px)<input inputMode="numeric" type="number" min="1" value={height} onChange={(e) => setHeight(e.target.value)} placeholder="Auto" className="focus-ring mt-1.5 w-full rounded-xl border border-stone-200 bg-white px-3 py-2.5 text-sm" /></label></div><label className="mt-3 flex cursor-pointer items-center gap-2 text-sm text-kiwi-ink/65"><input type="checkbox" checked={exact} onChange={(e) => setExact(e.target.checked)} /> Force exact width × height</label></div></details> : null}
          {isBusy ? <ProgressPanel label="Converting images…" progress={progress} /> : null}
          {state === 'done' && jobId ? <ResultPanel jobId={jobId} results={results} kind={kind ?? 'image_convert'} originalSize={files.length === 1 ? files[0].size : undefined} onReset={() => { reset(); setFiles([]) }} /> : null}
          {state === 'failed' ? <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-600">{errorMessage}</div> : null}
        </div>
      )}
    </PageShell>
  )
}
