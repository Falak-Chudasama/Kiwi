import { useState } from 'react'
import { CheckCircleIcon, DownloadIcon, PackageOpenIcon } from '../ui/icons'
import { downloadUrl, type JobResultFile } from '../../lib/api'
import { formatBytes } from './FileChip'

interface ResultPanelProps {
  jobId: string
  results: JobResultFile[]
  kind: string
  originalSize?: number
  onReset: () => void
}

function triggerNativeDownload(url: string, filename: string) {
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
}

export function ResultPanel({ jobId, results, originalSize, onReset }: ResultPanelProps) {
  const [downloadingAll, setDownloadingAll] = useState(false)
  const outputSize = results.length === 1 ? results[0].size : undefined
  const delta = originalSize && outputSize ? originalSize - outputSize : undefined
  const savedPercent = delta !== undefined && originalSize ? (delta / originalSize) * 100 : undefined
  const hasMultiple = results.length > 1

  const handleDownloadAll = async () => {
    setDownloadingAll(true)
    try {
      for (let index = 0; index < results.length; index += 1) {
        triggerNativeDownload(downloadUrl(jobId, index), results[index].name)
        if (index < results.length - 1) {
          await new Promise((resolve) => window.setTimeout(resolve, 200))
        }
      }
    } finally {
      setDownloadingAll(false)
    }
  }

  return (
    <div className="rounded-2xl border border-black/[0.06] bg-white p-6 shadow-soft animate-scale-in">
      <div className="flex items-center justify-between border-b border-stone-100 pb-4">
        <div className="flex items-center gap-2.5 text-base font-bold text-emerald-600">
          <CheckCircleIcon className="h-5 w-5" />
          <span>Processing Completed</span>
        </div>
        <button
          type="button"
          onClick={onReset}
          className="text-sm font-semibold text-stone-500 hover:text-stone-900 transition"
        >
          Convert another file
        </button>
      </div>

      {outputSize !== undefined && (
        <div className="mt-4 rounded-xl bg-stone-50 p-4 text-sm">
          <div className="flex items-center justify-between text-stone-600 font-medium">
            <span>Result Size</span>
            <span className="font-bold text-stone-900 text-base">{formatBytes(outputSize)}</span>
          </div>
          {savedPercent !== undefined && Math.abs(savedPercent) > 0.1 && (
            <div
              className={`mt-2 flex items-center justify-between font-bold ${
                savedPercent > 0 ? 'text-emerald-600' : 'text-stone-500'
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
        {results.map((result, index) => (
          <a
            key={`${result.name}-${index}`}
            href={downloadUrl(jobId, index)}
            download={result.name}
            className="focus-ring flex items-center justify-between gap-4 rounded-2xl border border-stone-200/90 bg-white px-5 py-4 transition hover:border-kiwi-flesh/50 hover:bg-stone-50 shadow-2xs"
          >
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm sm:text-base font-bold text-stone-900">{result.name}</p>
              <p className="text-xs sm:text-sm text-stone-500">{formatBytes(result.size)}</p>
            </div>
            <div className="flex items-center gap-2 rounded-xl bg-kiwi-flesh/10 px-4 py-2 text-sm font-bold text-kiwi-flesh-700">
              <DownloadIcon className="h-4 w-4" />
              <span>Download</span>
            </div>
          </a>
        ))}

        {hasMultiple && (
          <button
            type="button"
            onClick={handleDownloadAll}
            disabled={downloadingAll}
            className="focus-ring mt-4 flex w-full items-center justify-center gap-2.5 rounded-2xl bg-stone-900 py-4 text-sm sm:text-base font-bold text-white transition hover:bg-black disabled:opacity-50 shadow-soft"
          >
            <PackageOpenIcon className="h-5 w-5" />
            <span>{downloadingAll ? 'Triggering downloads…' : `Download all ${results.length} files`}</span>
          </button>
        )}
      </div>
    </div>
  )
}
