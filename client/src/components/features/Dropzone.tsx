import { useCallback, useRef, useState, type DragEvent } from 'react'
import { UploadCloudIcon } from '../ui/icons'

interface DropzoneProps {
  onFiles: (files: File[]) => void
  accept?: string
  multiple?: boolean
  hint: string
  preview?: React.ReactNode
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

  const deliver = useCallback((incoming: File[]) => {
    const filtered = incoming.filter((file) => matchesAccept(file, accept))
    if (filtered.length) onFiles(multiple ? filtered : [filtered[0]])
  }, [accept, multiple, onFiles])

  const handleDrop = useCallback((event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(false)
    deliver(Array.from(event.dataTransfer.files))
  }, [deliver])

  const handleSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    deliver(Array.from(event.target.files ?? []))
    event.target.value = ''
  }

  return (
    <div className="space-y-4">
      <div
        onDragOver={(event) => { event.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') inputRef.current?.click() }}
        className={`focus-ring flex cursor-pointer flex-col items-center justify-center gap-4 rounded-[2rem] border-2 border-dashed px-6 py-16 text-center transition ${isDragging ? 'border-kiwi-flesh bg-kiwi-flesh-50' : 'border-stone-200 bg-white hover:border-kiwi-flesh/60 hover:bg-kiwi-flesh-50/40'}`}
      >
        <div className="rounded-2xl bg-kiwi-flesh-100 p-4">
          <UploadCloudIcon className="h-7 w-7 text-kiwi-flesh-700" />
        </div>
        <div>
          <p className="font-heading text-lg font-semibold text-kiwi-ink">Drop {multiple ? 'files' : 'a file'} here</p>
          <p className="mt-1 text-sm text-kiwi-ink/50">or click to browse · {hint}</p>
        </div>
        <input ref={inputRef} type="file" accept={accept} multiple={multiple} onChange={handleSelect} className="hidden" />
      </div>
      {preview}
    </div>
  )
}
