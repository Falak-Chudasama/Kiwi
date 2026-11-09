import { useEffect, useState } from 'react'
import { ImageIcon } from '../ui/icons'
import { formatBytes } from './FileChip'

interface ImagePreviewProps {
  files: File[]
  maxPreviews?: number
}

function PreviewTile({ file }: { file: File }) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    // Only generate preview URL if the file is an image
    if (!file.type.startsWith('image/') && !file.name.match(/\.(jpg|jpeg|png|webp|avif|gif|bmp|ico|svg)$/i)) {
      setFailed(true)
      return
    }

    const url = URL.createObjectURL(file)
    setObjectUrl(url)
    setFailed(false)

    return () => {
      URL.revokeObjectURL(url)
    }
  }, [file])

  return (
    <div className="group overflow-hidden rounded-xl border border-black/[0.06] dark:border-white/[0.08] bg-white dark:bg-[#181915] shadow-soft transition hover:shadow-lift">
      <div className="flex aspect-[4/3] items-center justify-center overflow-hidden bg-stone-50/80 dark:bg-[#121310] p-2.5">
        {objectUrl && !failed ? (
          <img
            src={objectUrl}
            alt={file.name}
            onError={() => setFailed(true)}
            className="max-h-full max-w-full object-contain transition group-hover:scale-[1.02]"
            loading="lazy"
          />
        ) : (
          <div className="px-3 text-center text-[11px] font-medium text-stone-400 dark:text-stone-500">
            Preview unavailable
          </div>
        )}
      </div>
      <div className="px-3 py-2 border-t border-stone-100 dark:border-stone-800">
        <p className="truncate text-xs font-semibold text-stone-900 dark:text-stone-100">{file.name}</p>
        <p className="text-[10px] text-stone-400 dark:text-stone-500">{formatBytes(file.size)}</p>
      </div>
    </div>
  )
}

export function ImagePreview({ files, maxPreviews = 6 }: ImagePreviewProps) {
  if (!files.length) return null

  const visibleFiles = files.slice(0, maxPreviews)
  const remainingCount = files.length - maxPreviews

  return (
    <div className="rounded-2xl border border-black/[0.06] dark:border-white/[0.08] bg-stone-100/50 dark:bg-[#181915]/50 p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-stone-500 dark:text-stone-400">
          <ImageIcon className="h-3.5 w-3.5 text-stone-600 dark:text-stone-400" />
          <span>Selected Images ({files.length})</span>
        </div>
        {remainingCount > 0 && (
          <span className="text-xs font-medium text-stone-400 dark:text-stone-500">
            +{remainingCount} more
          </span>
        )}
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {visibleFiles.map((file, index) => (
          <PreviewTile key={`${file.name}-${file.size}-${index}`} file={file} />
        ))}
      </div>
    </div>
  )
}
