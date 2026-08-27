import { downloadUrl } from '../../lib/api'
import { CheckCircleIcon, DownloadIcon } from '../ui/icons'

interface ResultPanelProps {
  jobId: string
  fileCount: number
  onReset: () => void
}

export function ResultPanel({ jobId, fileCount, onReset }: ResultPanelProps) {
  return (
    <div className="rounded-2xl border border-kiwi-flesh-100 bg-kiwi-flesh-50 px-5 py-5">
      <div className="flex items-center gap-2.5 text-sm font-semibold text-kiwi-flesh-700">
        <CheckCircleIcon className="h-5 w-5" />
        Ready to download
      </div>

      <div className="mt-4 flex flex-col gap-2">
        {Array.from({ length: fileCount }).map((_, index) => (
          <a
            key={index}
            href={downloadUrl(jobId, index)}
            download
            className="focus-ring flex items-center justify-center gap-2 rounded-xl bg-kiwi-flesh px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-kiwi-flesh-600 active:bg-kiwi-flesh-700"
          >
            <DownloadIcon className="h-4 w-4" />
            {fileCount > 1 ? `Download file ${index + 1}` : 'Download file'}
          </a>
        ))}
      </div>

      <button
        type="button"
        onClick={onReset}
        className="focus-ring mt-3 w-full rounded-xl border border-kiwi-shell-50 bg-white px-4 py-2.5 text-sm font-medium text-kiwi-ink/70 transition hover:bg-kiwi-flesh-50"
      >
        Convert another file
      </button>
    </div>
  )
}
