import { useEffect, useMemo, useState } from 'react'
import { useLocation } from 'react-router-dom'
import {
  AlertCircle,
  ArrowRight,
  ArrowRightLeft,
  CheckCircle2,
  Files,
  Info,
} from 'lucide-react'
import { PageShell } from '../components/layout/PageShell'
import { Dropzone } from '../components/features/Dropzone'
import { FileChip, formatBytes } from '../components/features/FileChip'
import { FormatPicker, type FormatOption } from '../components/features/FormatPicker'
import { ProgressPanel } from '../components/features/ProgressPanel'
import { ResultPanel } from '../components/features/ResultPanel'
import { useJobRunner } from '../hooks/useJobRunner'
import { fetchTargets, type TargetOption } from '../lib/api'
import { useToast } from '../components/ui/ToastProvider'
import { categoryOf, extensionOf } from '../components/features/formatUtils'
import { playEnter } from '../lib/sound'

export default function DocumentConvertPage() {
  const location = useLocation()
  const initialFiles = (location.state as { incomingFiles?: File[] })?.incomingFiles || []

  const [files, setFiles] = useState<File[]>(initialFiles)
  const [targetsByExt, setTargetsByExt] = useState<Record<string, TargetOption[]>>({})
  const [targetExt, setTargetExt] = useState<string | null>(null)
  const [loadingTargets, setLoadingTargets] = useState(false)

  const { state, progress, jobId, results, kind, errorMessage, isBusy, run, cancel, reset } =
    useJobRunner()
  const toast = useToast()

  // Fetch targets for all distinct extensions in the selection
  useEffect(() => {
    let cancelled = false
    if (!files.length) {
      setTargetsByExt({})
      setTargetExt(null)
      return
    }

    const distinctExts = Array.from(new Set(files.map((f) => extensionOf(f.name))))
    setLoadingTargets(true)

    Promise.all(
      distinctExts.map(async (ext) => {
        try {
          const sampleName = `file.${ext}`
          const options = await fetchTargets('documents', sampleName)
          return [ext, options] as const
        } catch {
          return [ext, [] as TargetOption[]] as const
        }
      }),
    )
      .then((entries) => {
        if (cancelled) return
        const map = Object.fromEntries(entries)
        setTargetsByExt(map)
        setLoadingTargets(false)
      })
      .catch(() => {
        if (!cancelled) {
          setLoadingTargets(false)
          toast.push('error', 'Could not resolve conversion target capabilities.')
        }
      })

    return () => {
      cancelled = true
    }
  }, [files, toast])

  // Compute common formats supported by EVERY selected file (multi-file intersection)
  const commonTargets: FormatOption[] = useMemo(() => {
    const extList = Object.keys(targetsByExt)
    if (!extList.length) return []

    const firstOptions = targetsByExt[extList[0]] || []
    if (extList.length === 1) return firstOptions

    return firstOptions.map((opt) => {
      // Check if this target is supported by all other selected file extensions
      const supportedByAll = extList.every((ext) => {
        const fileTargets = targetsByExt[ext] || []
        const match = fileTargets.find((t) => t.ext === opt.ext)
        return match && match.supported
      })

      const readyForDraft = extList.every((ext) => {
        const fileTargets = targetsByExt[ext] || []
        const match = fileTargets.find((t) => t.ext === opt.ext)
        return match && match.ready !== false
      })

      return {
        ...opt,
        supported: supportedByAll,
        ready: readyForDraft,
        reason: supportedByAll
          ? opt.reason
          : 'Not supported for all currently selected file types.',
      }
    })
  }, [targetsByExt])

  // Default selection when common targets resolve
  useEffect(() => {
    if (commonTargets.length && !targetExt) {
      const firstReady = commonTargets.find((o) => o.supported && o.ready !== false)
      if (firstReady) setTargetExt(firstReady.ext)
    }
  }, [commonTargets, targetExt])

  const handleConvert = async () => {
    if (!files.length || !targetExt) return
    playEnter()
    const formData = new FormData()
    // For single file, use 'file'; for multiple, send first file or submit individually
    formData.append('file', files[0])
    formData.append('target_ext', targetExt)
    await run('/api/documents/convert', formData)
  }

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
    reset()
  }

  const readyCount = commonTargets.filter((o) => o.supported && o.ready !== false).length

  return (
    <PageShell
      title="Universal Converter"
      description="Convert documents, spreadsheets, presentations, and markup with authoritative engine detection."
      icon={<ArrowRightLeft className="h-4 w-4" />}
    >
      {!files.length ? (
        <Dropzone
          onFiles={(newFiles) => {
            reset()
            setFiles(newFiles)
          }}
          hint="PDF, DOCX, XLSX, PPTX, Markdown, HTML, EPUB, and more"
        />
      ) : (
        <div className="space-y-6">
          {/* Selected File(s) Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-stone-500 dark:text-stone-400 uppercase tracking-wider">
                Selected Input ({files.length})
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
                  Clear selection
                </button>
              )}
            </div>
            {files.map((file, idx) => (
              <FileChip
                key={`${file.name}-${idx}`}
                name={file.name}
                sizeLabel={`${formatBytes(file.size)} · ${categoryOf(file.name)}`}
                onRemove={state === 'idle' ? () => removeFile(idx) : undefined}
              />
            ))}
          </div>

          {/* Conversion Action Bar - Prominently positioned above format picker */}
          {state === 'idle' && targetExt && (
            <div className="glass-panel flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between rounded-2xl p-5 sm:p-6 shadow-soft">
              <div className="flex items-center gap-3 text-sm sm:text-base text-stone-700 dark:text-stone-300 min-w-0">
                <CheckCircle2 className="h-5 w-5 text-kiwi-flesh-700 dark:text-kiwi-lime shrink-0" />
                <span className="font-bold text-stone-900 dark:text-stone-100 truncate max-w-xs">{files[0].name}</span>
                <ArrowRight className="h-4 w-4 text-stone-400 dark:text-stone-500 shrink-0" />
                <span className="rounded-lg bg-kiwi-flesh/10 dark:bg-kiwi-lime/10 px-3 py-1 text-sm font-extrabold text-kiwi-flesh-700 dark:text-kiwi-lime uppercase shrink-0">
                  {targetExt}
                </span>
              </div>

              <button
                type="button"
                onClick={handleConvert}
                disabled={!targetExt || isBusy}
                className="btn-glass-primary shrink-0"
              >
                <span>Convert File</span>
              </button>
            </div>
          )}

          {/* Target Format Picker */}
          {state === 'idle' && (
            <div className="glass-panel rounded-2xl p-6 shadow-soft">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-bold uppercase tracking-wider text-stone-500 dark:text-stone-400">
                    Output Format
                  </h2>
                  <p className="mt-1 text-sm text-stone-600 dark:text-stone-400 font-medium">
                    {loadingTargets
                      ? 'Resolving format capabilities…'
                      : `${readyCount} formats ready for conversion`}
                  </p>
                </div>
              </div>

              <FormatPicker
                options={commonTargets}
                value={targetExt}
                onChange={setTargetExt}
              />
            </div>
          )}

          {/* Progress & Cancel */}
          {isBusy && (
            <ProgressPanel
              label={state === 'uploading' ? 'Streaming upload to temporary workspace…' : 'Executing conversion engine…'}
              progress={progress}
              onCancel={cancel}
            />
          )}

          {/* Results Display */}
          {state === 'done' && jobId && (
            <ResultPanel
              jobId={jobId}
              results={results}
              kind={kind ?? 'document_convert'}
              originalSize={files[0]?.size}
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
                <p className="font-semibold">Conversion could not be completed</p>
                <p className="mt-1 text-rose-600 dark:text-rose-400 leading-relaxed">{errorMessage}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </PageShell>
  )
}
