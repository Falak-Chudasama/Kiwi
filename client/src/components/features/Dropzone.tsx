import { useCallback, useRef, useState, type DragEvent } from 'react'
import { UploadCloudIcon } from '../ui/icons'

interface DropzoneProps {
  onFiles: (files: File[]) => void
  accept?: string
  multiple?: boolean
  hint: string
}

export function Dropzone({ onFiles, accept, multiple = false, hint }: DropzoneProps) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault()
      setIsDragging(false)
      const files = Array.from(e.dataTransfer.files)
      if (files.length) onFiles(multiple ? files : [files[0]])
    },
    [multiple, onFiles],
  )

  const handleSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? [])
    if (files.length) onFiles(multiple ? files : [files[0]])
    e.target.value = ''
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault()
        setIsDragging(true)
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click()
      }}
      className={`focus-ring flex cursor-pointer flex-col items-center justify-center gap-3 rounded-card border-2 border-dashed px-6 py-14 text-center transition ${
        isDragging
          ? 'border-kiwi-flesh bg-kiwi-flesh-50'
          : 'border-kiwi-shell-50 bg-white hover:border-kiwi-flesh/50 hover:bg-kiwi-flesh-50/40'
      }`}
    >
      <div className="rounded-full bg-kiwi-flesh-100 p-4">
        <UploadCloudIcon className="h-6 w-6 text-kiwi-flesh-700" />
      </div>
      <div>
        <p className="font-heading text-base font-semibold text-kiwi-ink">
          Drop {multiple ? 'files' : 'a file'} here, or click to browse
        </p>
        <p className="mt-1 text-sm text-kiwi-ink/50">{hint}</p>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleSelect}
        className="hidden"
      />
    </div>
  )
}
