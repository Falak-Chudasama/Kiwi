import { CheckCircleIcon, DownloadIcon, PackageOpenIcon } from '../ui/icons'
import { downloadUrl, type JobResultFile } from '../../lib/api'
import { formatBytes } from './FileChip'
import { useState } from 'react'

interface ResultPanelProps {
  jobId: string
  results: JobResultFile[]
  kind: string
  originalSize?: number
  onReset: () => void
}

async function downloadAllFiles(jobId: string, results: JobResultFile[]) {
  for (let index = 0; index < results.length; index += 1) {
    const response = await fetch(downloadUrl(jobId, index))
    if (!response.ok) throw new Error(`Could not download ${results[index].name}.`)
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = results[index].name
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    URL.revokeObjectURL(url)
    if (index < results.length - 1) await new Promise((resolve) => window.setTimeout(resolve, 160))
  }
}

export function ResultPanel({ jobId, results, kind, originalSize, onReset }: ResultPanelProps) {
  const [downloadingAll, setDownloadingAll] = useState(false)
  const [downloadError, setDownloadError] = useState<string | null>(null)
  const outputSize = results.length === 1 ? results[0].size : undefined
  const delta = originalSize && outputSize ? originalSize - outputSize : undefined
  const savedPercent = delta !== undefined && originalSize ? (delta / originalSize) * 100 : undefined
  const canDownloadAll = kind === 'archive_extract' && results.length > 1

  const handleDownloadAll = async () => {
    setDownloadingAll(true)
    setDownloadError(null)
    try {
      await downloadAllFiles(jobId, results)
    } catch (error) {
      setDownloadError(error instanceof Error ? error.message : 'Some files could not be downloaded.')
    } finally {
      setDownloadingAll(false)
    }
  }

  return (
    <div className="rounded-[1.5rem] border border-kiwi-flesh-100 bg-kiwi-flesh-50/80 p-5 shadow-soft">
      <div className="flex items-center gap-2.5 text-sm font-bold text-kiwi-flesh-700">
        <CheckCircleIcon className="h-5 w-5" /> Ready
      </div>

      {outputSize !== undefined ? (
        <div className="mt-4 rounded-2xl bg-white px-4 py-3 text-sm">
          <div className="flex items-center justify-between gap-3">
            <span className="text-kiwi-ink/55">Output size</span>
            <span className="font-bold text-kiwi-ink">{formatBytes(outputSize)}</span>
          </div>
          {savedPercent !== undefined ? (
            <div className={`mt-1 flex items-center justify-between text-xs ${savedPercent >= 0 ? 'text-kiwi-flesh-700' : 'text-red-500'}`}>
              <span>{savedPercent >= 0 ? 'Size change' : 'Output is larger'}</span>
              <span>{savedPercent >= 0 ? `${savedPercent.toFixed(1)}% smaller` : `${Math.abs(savedPercent).toFixed(1)}% larger`}</span>
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="mt-4 space-y-2">
        {results.map((result, index) => (
          <a key={`${result.name}-${index}`} href={downloadUrl(jobId, index)} download className="focus-ring flex items-center gap-3 rounded-2xl border border-stone-100 bg-white px-4 py-3 transition hover:border-kiwi-flesh/30 hover:shadow-soft">
            <div className="rounded-xl bg-kiwi-flesh-100 p-2 text-kiwi-flesh-700"><DownloadIcon className="h-4 w-4" /></div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-kiwi-ink">{result.name}</p>
              <p className="text-xs text-kiwi-ink/45">{formatBytes(result.size)}</p>
            </div>
            <span className="text-xs font-bold text-kiwi-flesh-700">Download</span>
          </a>
        ))}

        {canDownloadAll ? (
          <button
            type="button"
            onClick={handleDownloadAll}
            disabled={downloadingAll}
            className="focus-ring flex w-full items-center gap-3 rounded-2xl bg-kiwi-ink px-4 py-3 text-left text-white transition hover:bg-kiwi-ink-600 disabled:cursor-wait disabled:opacity-70"
          >
            <div className="rounded-xl bg-white/10 p-2"><PackageOpenIcon className="h-4 w-4" /></div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold">{downloadingAll ? 'Downloading files…' : 'Download all'}</p>
              <p className="text-xs text-white/55">{results.length} extracted files, downloaded individually</p>
            </div>
            <DownloadIcon className="h-4 w-4" />
          </button>
        ) : null}
      </div>

      {downloadError ? <p className="mt-3 rounded-xl border border-red-100 bg-red-50 px-3 py-2 text-xs text-red-600">{downloadError}</p> : null}

      <button type="button" onClick={onReset} className="focus-ring mt-3 w-full rounded-xl border border-stone-200 bg-white px-4 py-2.5 text-sm font-semibold text-kiwi-ink/65 transition hover:bg-stone-50">
        Start another operation
      </button>
    </div>
  )
}
