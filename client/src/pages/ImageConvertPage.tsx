import { useEffect, useState } from 'react'
import {
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  Image as ImageIcon,
  Sliders,
} from 'lucide-react'
import { PageShell } from '../components/layout/PageShell'
import { Dropzone } from '../components/features/Dropzone'
import { FileChip, formatBytes } from '../components/features/FileChip'
import { FormatPicker, type FormatOption } from '../components/features/FormatPicker'
import { ImagePreview } from '../components/features/ImagePreview'
import { ProgressPanel } from '../components/features/ProgressPanel'
import { ResultPanel } from '../components/features/ResultPanel'
import { TextField } from '../components/ui/TextField'
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
  const [exactStretch, setExactStretch] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)

  const { state, progress, jobId, results, kind, errorMessage, isBusy, run, cancel, reset } =
    useJobRunner()
  const toast = useToast()

  useEffect(() => {
    if (!files.length) {
      setTargets([])
      setTargetExt(null)
      return
    }

    fetchTargets('images', files[0].name)
      .then((options) => {
        setTargets(options)
        const firstReady = options.find((o) => o.supported && o.ready !== false)
        if (firstReady && !targetExt) setTargetExt(firstReady.ext)
      })
      .catch(() => toast.push('error', 'Could not resolve image target formats.'))
  }, [files, targetExt, toast])

  const handleConvert = async () => {
    if (!files.length || !targetExt) return
    const formData = new FormData()
    files.forEach((f) => formData.append('files', f))
    formData.append('target_ext', targetExt)
    if (width) formData.append('width', width)
    if (height) formData.append('height', height)
    formData.append('fit_mode', exactStretch ? 'exact' : 'contain')

    await run('/api/images/convert', formData)
  }

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
    reset()
  }

  return (
    <PageShell
      title="Image Tools"
      description="Batch convert, resize, preview, and encode modern raster and vector image formats."
      icon={<ImageIcon className="h-4 w-4" />}
    >
      {!files.length ? (
        <Dropzone
          onFiles={(newFiles) => {
            reset()
            setFiles(newFiles)
          }}
          multiple
          accept={IMAGE_ACCEPT}
          hint="JPG, PNG, WebP, AVIF, HEIC, TIFF, BMP, GIF, SVG"
        />
      ) : (
        <div className="space-y-6">
          {/* Bounded Image Preview Strip */}
          <ImagePreview files={files} maxPreviews={6} />

          {/* Selected Files List */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-stone-500 uppercase tracking-wider">
                Input Images ({files.length})
              </span>
              {state === 'idle' && (
                <button
                  type="button"
                  onClick={() => {
                    reset()
                    setFiles([])
                  }}
                  className="text-sm font-semibold text-stone-400 hover:text-stone-700 transition"
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

          {/* Target Format Picker */}
          {state === 'idle' && (
            <div className="rounded-2xl border border-black/[0.06] bg-white p-6 shadow-soft">
              <h2 className="mb-4 text-sm font-bold uppercase tracking-wider text-stone-500">
                Target Image Format
              </h2>
              <FormatPicker
                options={targets}
                value={targetExt}
                onChange={setTargetExt}
                priorityGroup="Images"
              />
            </div>
          )}

          {/* Collapsible Advanced Resizing Section */}
          {state === 'idle' && (
            <div className="overflow-hidden rounded-2xl border border-black/[0.06] bg-white shadow-soft transition">
              <button
                type="button"
                onClick={() => setShowAdvanced((prev) => !prev)}
                className="flex w-full items-center justify-between p-5 text-left transition hover:bg-stone-50/50"
              >
                <div className="flex items-center gap-2.5 text-sm sm:text-base font-bold text-stone-900">
                  <Sliders className="h-4 w-4 text-stone-600" />
                  <span>Resizing & Dimension Controls (Optional)</span>
                </div>
                <ChevronDown
                  className={`h-4 w-4 text-stone-400 transition-transform duration-200 ${
                    showAdvanced ? 'rotate-180' : ''
                  }`}
                />
              </button>

              {showAdvanced && (
                <div className="border-t border-stone-100 p-5 text-sm space-y-4 animate-slide-up">
                  <p className="text-stone-600 leading-relaxed text-sm">
                    Leave one dimension blank to preserve the natural aspect ratio automatically.
                  </p>

                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <label className="block text-sm font-bold text-stone-700 mb-1.5">
                        Width (px)
                      </label>
                      <TextField
                        type="number"
                        min="1"
                        placeholder="Auto"
                        value={width}
                        onChange={(e) => setWidth(e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-stone-700 mb-1.5">
                        Height (px)
                      </label>
                      <TextField
                        type="number"
                        min="1"
                        placeholder="Auto"
                        value={height}
                        onChange={(e) => setHeight(e.target.value)}
                      />
                    </div>
                  </div>

                  <label className="flex items-center gap-2.5 cursor-pointer text-stone-700 font-medium">
                    <input
                      type="checkbox"
                      checked={exactStretch}
                      onChange={(e) => setExactStretch(e.target.checked)}
                      className="h-4 w-4 rounded border-stone-300 text-kiwi-flesh focus:ring-kiwi-flesh"
                    />
                    <span className="text-sm">
                      Force exact dimensions (stretch image if ratio differs)
                    </span>
                  </label>
                </div>
              )}
            </div>
          )}

          {/* Action Bar */}
          {state === 'idle' && targetExt && (
            <button
              type="button"
              onClick={handleConvert}
              disabled={isBusy}
              className="focus-ring flex w-full items-center justify-center gap-2 rounded-2xl bg-kiwi-flesh py-4 text-sm sm:text-base font-bold text-white shadow-soft transition hover:bg-kiwi-flesh-600"
            >
              <span>Convert {files.length > 1 ? `${files.length} Images` : 'Image'} to {targetExt.toUpperCase()}</span>
            </button>
          )}

          {/* Progress */}
          {isBusy && (
            <ProgressPanel
              label="Encoding image files…"
              progress={progress}
              onCancel={cancel}
            />
          )}

          {/* Results */}
          {state === 'done' && jobId && (
            <ResultPanel
              jobId={jobId}
              results={results}
              kind={kind ?? 'image_convert'}
              originalSize={files.length === 1 ? files[0].size : undefined}
              onReset={() => {
                reset()
                setFiles([])
              }}
            />
          )}

          {/* Error */}
          {state === 'failed' && (
            <div className="flex items-start gap-3 rounded-2xl border border-rose-100 bg-rose-50/80 p-4 text-xs text-rose-700 animate-slide-up">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-semibold">Image processing failed</p>
                <p className="mt-1 text-rose-600">{errorMessage}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </PageShell>
  )
}
