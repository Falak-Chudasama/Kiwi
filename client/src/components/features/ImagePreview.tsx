import { useEffect, useMemo, useState } from 'react'
import { ImageIcon } from '../ui/icons'
import { formatBytes } from './FileChip'

interface ImagePreviewProps { files: File[] }

function PreviewTile({ file, url }: { file: File; url: string }) {
  const [failed, setFailed] = useState(false)
  return <div className="overflow-hidden rounded-2xl border border-white bg-white">
    <div className="flex aspect-[4/3] items-center justify-center overflow-hidden bg-slate-50 p-3">
      {!failed ? <img src={url} alt={file.name} onError={() => setFailed(true)} className="max-h-full max-w-full object-contain" /> : <div className="px-4 text-center text-xs font-semibold text-kiwi-ink/40">Preview unavailable in this browser</div>}
    </div>
    <div className="px-3 py-2"><p className="truncate text-xs font-semibold text-kiwi-ink">{file.name}</p><p className="text-[11px] text-kiwi-ink/45">{formatBytes(file.size)}</p></div>
  </div>
}

export function ImagePreview({ files }: ImagePreviewProps) {
  const urls = useMemo(() => files.map((file) => URL.createObjectURL(file)), [files])
  useEffect(() => () => urls.forEach((url) => URL.revokeObjectURL(url)), [urls])
  if (!files.length) return null
  return <div className="rounded-3xl border border-sky-100 bg-sky-50/60 p-4">
    <div className="mb-3 flex items-center gap-2 text-sm font-bold text-sky-700"><ImageIcon className="h-4 w-4" /> Preview</div>
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">{files.map((file, index) => <PreviewTile key={`${file.name}-${index}`} file={file} url={urls[index]} />)}</div>
  </div>
}
