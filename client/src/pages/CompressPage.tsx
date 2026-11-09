import { useState } from 'react'
import { AlertCircle, Minimize2, ShieldCheck } from 'lucide-react'
import { PageShell } from '../components/layout/PageShell'
import { Dropzone } from '../components/features/Dropzone'
import { FileChip, formatBytes } from '../components/features/FileChip'
import { ProgressPanel } from '../components/features/ProgressPanel'
import { ResultPanel } from '../components/features/ResultPanel'
import { useJobRunner } from '../hooks/useJobRunner'

type CompressionLevel = 'low' | 'medium' | 'high' | 'extreme'

const LEVELS: {
  value: CompressionLevel
  label: string
  desc: string
}[] = [
  { value: 'low', label: 'Light', desc: 'Minimal compression, pristine quality preservation.' },
  { value: 'medium', label: 'Balanced (Recommended)', desc: 'Optimal size reduction while keeping sharp text and vectors.' },
  { value: 'high', label: 'Strong', desc: 'Aggressive image compression and font stream deduplication.' },
  { value: 'extreme', label: 'Maximum', desc: 'Maximum deflate effort and heavy image quantization.' },
]

export default function CompressPage() {
  const [file, setFile] = useState<File | null>(null)
  const [level, setLevel] = useState<CompressionLevel>('medium')

  const { state, progress, jobId, results, kind, errorMessage, isBusy, run, cancel, reset } =
    useJobRunner()

  const handleFiles = (incoming: File[]) => {
    reset()
    setFile(incoming[0])
  }

  const handleCompress = async () => {
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    formData.append('level', level)
    await run('/api/compress', formData)
  }

  return (
    <PageShell
      title="File Compression"
      description="Optimize PDF documents, images, and Office packages with guaranteed no-larger output."
      icon={<Minimize2 className="h-4 w-4" />}
    >
      {!file ? (
        <Dropzone
          onFiles={handleFiles}
          accept=".pdf,.jpg,.jpeg,.png,.webp,.tiff,.tif,.docx,.pptx,.xlsx,.odt,.ods,.odp"
          hint="PDF, JPG, PNG, WEBP, TIFF, DOCX, PPTX, XLSX, ODT, ODS, ODP"
        />
      ) : (
        <div className="space-y-6">
          <FileChip
            name={file.name}
            sizeLabel={formatBytes(file.size)}
            onRemove={
              state === 'idle'
                ? () => {
                    reset()
                    setFile(null)
                  }
                : undefined
            }
          />

          {/* Safety Notice */}
          <div className="flex items-start gap-3 rounded-2xl border border-black/[0.05] dark:border-white/[0.08] bg-white dark:bg-[#181915] p-4.5 text-sm text-stone-600 dark:text-stone-300 shadow-xs">
            <ShieldCheck className="h-5 w-5 text-emerald-600 dark:text-kiwi-lime shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-stone-900 dark:text-stone-100">Non-destructive preservation</p>
              <p className="text-stone-500 dark:text-stone-400 mt-1 leading-relaxed">
                PDF text, hyperlinks, forms, and vector curves remain intact without rasterization. If an operation would make a file larger, the original size is preserved.
              </p>
            </div>
          </div>

          {/* Compression Level Selector */}
          {state === 'idle' && (
            <div className="rounded-2xl border border-black/[0.06] dark:border-white/[0.08] bg-white dark:bg-[#181915] p-6 shadow-soft space-y-4">
              <h2 className="text-sm font-bold uppercase tracking-wider text-stone-500 dark:text-stone-400">
                Optimization Strength
              </h2>

              <div className="grid gap-3 sm:grid-cols-2">
                {LEVELS.map((item) => (
                  <button
                    key={item.value}
                    type="button"
                    onClick={() => setLevel(item.value)}
                    className={`flex flex-col rounded-2xl border p-4 text-left transition ${
                      level === item.value
                        ? 'border-kiwi-flesh dark:border-kiwi-lime bg-kiwi-flesh/5 dark:bg-kiwi-lime/10 ring-2 ring-kiwi-flesh/30 dark:ring-kiwi-lime/30 shadow-xs'
                        : 'border-stone-200/90 dark:border-white/[0.08] bg-white dark:bg-[#1C1D18] hover:bg-stone-50 dark:hover:bg-[#22231E] shadow-2xs'
                    }`}
                  >
                    <span className="text-sm sm:text-base font-bold text-stone-900 dark:text-stone-100">{item.label}</span>
                    <span className="mt-1.5 text-xs sm:text-sm text-stone-500 dark:text-stone-400 leading-relaxed">
                      {item.desc}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Action Trigger */}
          {state === 'idle' && (
            <button
              type="button"
              onClick={handleCompress}
              disabled={isBusy}
              className="focus-ring flex w-full items-center justify-center gap-2 rounded-2xl bg-kiwi-flesh py-4 text-sm sm:text-base font-bold text-white shadow-soft transition hover:bg-kiwi-flesh-600"
            >
              <span>Compress File</span>
            </button>
          )}

          {/* Progress */}
          {isBusy && (
            <ProgressPanel
              label="Optimizing file structures and streams…"
              progress={progress}
              onCancel={cancel}
            />
          )}

          {/* Results */}
          {state === 'done' && jobId && (
            <ResultPanel
              jobId={jobId}
              results={results}
              kind={kind ?? 'compress_file'}
              originalSize={file.size}
              onReset={() => {
                reset()
                setFile(null)
              }}
            />
          )}

          {/* Error Message */}
          {state === 'failed' && (
            <div className="flex items-start gap-3 rounded-2xl border border-rose-100 dark:border-rose-900/50 bg-rose-50/80 dark:bg-rose-950/40 p-4 text-xs text-rose-700 dark:text-rose-300 animate-slide-up">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-semibold">Compression failed</p>
                <p className="mt-1 text-rose-600 dark:text-rose-400">{errorMessage}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </PageShell>
  )
}
