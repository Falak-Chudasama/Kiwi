import { useCallback, useRef, useState, type DragEvent, type ReactNode } from 'react'
import { UploadCloudIcon } from '../ui/icons'

interface DropzoneProps {
  onFiles: (files: File[]) => void
  accept?: string
  multiple?: boolean
  hint: string
  preview?: ReactNode
}

function matchesAccept(file: File, accept?: string): boolean {
  if (!accept) return true
  const rules = accept.split(',').map((item) => item.trim().toLowerCase()).filter(Boolean)
  const type = file.type.toLowerCase()
  const name = file.name.toLowerCase()
  const extension = name.includes('.') ? `.${name.split('.').pop()}` : ''

  return rules.some((rule) => {
    if (rule === '*/*') return true
    if (rule.endsWith('/*')) return type.startsWith(rule.slice(0, -1))
    if (rule.startsWith('.')) return extension === rule || name.endsWith(rule)
    return type === rule
  })
}

export function Dropzone({ onFiles, accept, multiple = false, hint, preview }: DropzoneProps) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const deliver = useCallback(
    (incoming: File[]) => {
      const filtered = incoming.filter((file) => matchesAccept(file, accept))
      if (filtered.length) onFiles(multiple ? filtered : [filtered[0]])
    },
    [accept, multiple, onFiles],
  )

  const handleDrop = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault()
      setIsDragging(false)
      deliver(Array.from(event.dataTransfer.files))
    },
    [deliver],
  )

  const handleSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    deliver(Array.from(event.target.files ?? []))
    event.target.value = ''
  }

  return (
    <div className="space-y-4">
      <div
        onDragOver={(event) => {
          event.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        aria-label="Upload files by dropping or clicking"
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault()
            inputRef.current?.click()
          }
        }}
        className={`focus-ring flex cursor-pointer flex-col items-center justify-center gap-4 rounded-3xl border-2 border-dashed px-8 py-16 text-center transition ${
          isDragging
            ? 'border-kiwi-flesh bg-kiwi-flesh-50/70 scale-[0.99]'
            : 'border-stone-300/80 bg-white hover:border-kiwi-flesh/60 hover:bg-stone-50/60 shadow-soft'
        }`}
      >
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-stone-100 text-stone-700 transition group-hover:scale-105 shadow-2xs">
          <UploadCloudIcon className="h-8 w-8 text-stone-800" />
        </div>

        <div>
          <p className="text-base sm:text-lg font-bold text-stone-900 font-sans">
            Drop {multiple ? 'files' : 'a file'} here, or <span className="text-kiwi-flesh-700 underline underline-offset-4">browse</span>
          </p>
          <p className="mt-2 text-sm text-stone-500 font-sans">{hint}</p>
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
      {preview}
    </div>
  )
}
