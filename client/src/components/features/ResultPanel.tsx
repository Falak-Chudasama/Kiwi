import { useState } from 'react'
import { CheckCircleIcon, DownloadIcon, PackageOpenIcon } from '../ui/icons'
import { downloadUrl, downloadFileBlob, type JobResultFile } from '../../lib/api'
import { formatBytes } from './FileChip'
import { MarqueeText } from '../ui/MarqueeText'
import { useToast } from '../ui/ToastProvider'
import { playFailed, playNotification, playBack } from '../../lib/sound'

interface ResultPanelProps {
  jobId: string
  results: JobResultFile[]
  kind: string
  originalSize?: number
  onReset: () => void
}

export function ResultPanel({ jobId, results = [], originalSize, onReset, kind }: ResultPanelProps) {
  const [downloadingAll, setDownloadingAll] = useState(false)
  const [downloadingIndices, setDownloadingIndices] = useState<Set<number>>(new Set())
  const toast = useToast()

  const safeResults = results ?? []
  const outputSize = safeResults.length === 1 ? safeResults[0]?.size : undefined
  const delta = originalSize && outputSize ? originalSize - outputSize : undefined
  const savedPercent = delta !== undefined && originalSize ? (delta / originalSize) * 100 : undefined
  const hasMultiple = safeResults.length > 1

  const handleDownloadSingle = async (e: React.MouseEvent, index: number, filename: string) => {
    e.preventDefault()
    if (!jobId || !jobId.trim()) {
      toast.push('error', 'Job ID is missing. Cannot download file.')
      playFailed()
      return
    }

    setDownloadingIndices((prev) => new Set(prev).add(index))
    try {
      const url = downloadUrl(jobId, index)
      await downloadFileBlob(url, filename)
      playNotification()
    } catch (err: any) {
      playFailed()
      toast.push('error', err.message || 'Failed to download file.')
    } finally {
      setDownloadingIndices((prev) => {
        const next = new Set(prev)
        next.delete(index)
        return next
      })
    }
  }

  const handleDownloadAll = async () => {
    if (!jobId || !jobId.trim()) {
      toast.push('error', 'Job ID is missing. Cannot download.')
      playFailed()
      return
    }

    setDownloadingAll(true)
    try {
      for (let index = 0; index < safeResults.length; index += 1) {
        const url = downloadUrl(jobId, index)
        await downloadFileBlob(url, safeResults[index].name)
        if (index < safeResults.length - 1) {
          await new Promise((resolve) => window.setTimeout(resolve, 300))
        }
      }
      playNotification()
      toast.push('success', `All ${safeResults.length} files downloaded successfully.`)
    } catch (err: any) {
      playFailed()
      toast.push('error', err.message || 'Error occurred while downloading files.')
    } finally {
      setDownloadingAll(false)
    }
  }

  return (
    <div className="glass-panel rounded-3xl p-6 sm:p-7 shadow-lift animate-scale-in">
      <div className="flex items-center justify-between border-b border-black/[0.06] dark:border-white/[0.08] pb-4">
        <div className="flex items-center gap-2.5 text-base font-bold text-emerald-600 dark:text-kiwi-lime">
          <CheckCircleIcon className="h-5 w-5" />
          <span>{kind === 'scanner_process' ? 'Scan Completed' : 'Processing Completed'}</span>
        </div>
        <button
          type="button"
          onClick={() => {
            playBack()
            onReset()
          }}
          className="text-sm font-semibold text-stone-500 dark:text-stone-400 hover:text-stone-900 dark:hover:text-stone-100 transition"
        >
          {kind === 'scanner_process' ? 'Scan another document' : 'Convert another file'}
        </button>
      </div>

      {outputSize !== undefined && (
        <div className="mt-4 rounded-2xl bg-white/50 dark:bg-black/20 p-4 text-sm border border-black/[0.04] dark:border-white/[0.04]">
          <div className="flex items-center justify-between text-stone-600 dark:text-stone-300 font-medium">
            <span>Result Size</span>
            <span className="font-bold text-stone-900 dark:text-stone-100 text-base">{formatBytes(outputSize)}</span>
          </div>
          {savedPercent !== undefined && Math.abs(savedPercent) > 0.1 && (
            <div
              className={`mt-2 flex items-center justify-between font-bold ${
                savedPercent > 0 ? 'text-emerald-600 dark:text-kiwi-lime' : 'text-stone-500 dark:text-stone-400'
              }`}
            >
              <span>{savedPercent > 0 ? 'Saved' : 'Difference'}</span>
              <span>
                {savedPercent > 0
                  ? `${savedPercent.toFixed(1)}% smaller`
                  : `${Math.abs(savedPercent).toFixed(1)}% larger`}
              </span>
            </div>
          )}
        </div>
      )}

      <div className="mt-5 space-y-2.5">
        {safeResults.map((result, index) => {
          const isDownloadingThis = downloadingIndices.has(index)
          return (
            <a
              key={`${result.name}-${index}`}
              href={downloadUrl(jobId, index)}
              download={result.name}
              onClick={(e) => handleDownloadSingle(e, index, result.name)}
              className="focus-ring btn-interactive flex items-center justify-between gap-4 rounded-2xl border border-stone-200/90 dark:border-white/[0.08] bg-white/70 dark:bg-[#1C1D18]/70 px-5 py-4 transition hover:border-kiwi-flesh/50 dark:hover:border-kiwi-lime/50 hover:bg-white dark:hover:bg-[#22231E] shadow-2xs backdrop-blur-md"
            >
              <div className="min-w-0 flex-1">
                <MarqueeText
                  text={result.name}
                  className="text-sm sm:text-base font-bold text-stone-900 dark:text-stone-100"
                />
                <p className="text-xs sm:text-sm text-stone-500 dark:text-stone-400 mt-0.5">{formatBytes(result.size)}</p>
              </div>
              <div className="flex items-center gap-2 rounded-xl bg-kiwi-flesh/10 dark:bg-kiwi-lime/10 px-4 py-2 text-sm font-bold text-kiwi-flesh-700 dark:text-kiwi-lime shrink-0">
                {isDownloadingThis ? (
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-kiwi-flesh dark:border-kiwi-lime border-t-transparent" />
                ) : (
                  <DownloadIcon className="h-4 w-4" />
                )}
                <span>{isDownloadingThis ? 'Saving…' : 'Download'}</span>
              </div>
            </a>
          )
        })}

        {hasMultiple && (
          <div className="flex justify-end mt-4">
            <button
              type="button"
              onClick={handleDownloadAll}
              disabled={downloadingAll}
              className="btn-glass-primary w-full sm:w-auto"
            >
              {downloadingAll ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
              ) : (
                <PackageOpenIcon className="h-4 w-4" />
              )}
              <span>{downloadingAll ? 'Saving downloads…' : `Download all ${results.length} files`}</span>
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
