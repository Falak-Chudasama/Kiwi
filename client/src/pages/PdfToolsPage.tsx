import { useState } from 'react'
import {
  FileType2,
  Image as ImageIcon,
  Layers3,
  Lock,
  RotateCw,
  ScanText,
  Scissors,
  Stamp,
  Unlock,
} from 'lucide-react'

import { PageShell } from '../components/layout/PageShell'
import { Dropzone } from '../components/features/Dropzone'
import { FileChip, formatBytes } from '../components/features/FileChip'
import { ProgressPanel } from '../components/features/ProgressPanel'
import { ResultPanel } from '../components/features/ResultPanel'
import { PdfOperationTile } from '../components/features/PdfOperationTile'
import { Popup } from '../components/ui/Popup'
import { TextField } from '../components/ui/TextField'
import { useJobRunner } from '../hooks/useJobRunner'


type Operation =
  | 'merge'
  | 'split'
  | 'to_images'
  | 'from_images'
  | 'rotate'
  | 'protect'
  | 'unlock'
  | 'watermark'
  | 'ocr'

const OPERATIONS: {
  value: Operation
  label: string
  icon: JSX.Element
  multiple: boolean
}[] = [
  { value: 'merge', label: 'Merge', icon: <Layers3 className="h-5 w-5" />, multiple: true },
  { value: 'split', label: 'Split', icon: <Scissors className="h-5 w-5" />, multiple: false },
  { value: 'to_images', label: 'PDF → Images', icon: <ImageIcon className="h-5 w-5" />, multiple: false },
  { value: 'from_images', label: 'Images → PDF', icon: <ImageIcon className="h-5 w-5" />, multiple: true },
  { value: 'rotate', label: 'Rotate', icon: <RotateCw className="h-5 w-5" />, multiple: false },
  { value: 'protect', label: 'Protect', icon: <Lock className="h-5 w-5" />, multiple: false },
  { value: 'unlock', label: 'Unlock', icon: <Unlock className="h-5 w-5" />, multiple: false },
  { value: 'watermark', label: 'Watermark', icon: <Stamp className="h-5 w-5" />, multiple: false },
  { value: 'ocr', label: 'OCR', icon: <ScanText className="h-5 w-5" />, multiple: false },
]

const ENDPOINTS: Record<Operation, string> = {
  merge: '/api/pdf/merge',
  split: '/api/pdf/split',
  to_images: '/api/pdf/to-images',
  from_images: '/api/pdf/from-images',
  rotate: '/api/pdf/rotate',
  protect: '/api/pdf/protect',
  unlock: '/api/pdf/unlock',
  watermark: '/api/pdf/watermark',
  ocr: '/api/pdf/ocr',
}

function parseRanges(value: string): number[][] {
  const ranges = value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => {
      if (item.includes('-')) {
        const [start, end] = item.split('-').map(Number)
        if (!Number.isInteger(start) || !Number.isInteger(end) || start < 1 || end < start) {
          throw new Error('Use ranges like 1-3,5-7.')
        }
        return [start, end]
      }
      const page = Number(item)
      if (!Number.isInteger(page) || page < 1) {
        throw new Error('Use pages like 1,2,4 or ranges like 1-3.')
      }
      return [page, page]
    })

  if (!ranges.length) {
    throw new Error('Enter at least one page or range.')
  }

  return ranges
}

export default function PdfToolsPage() {
  const [operation, setOperation] = useState<Operation>('merge')
  const [files, setFiles] = useState<File[]>([])
  const [popupOpen, setPopupOpen] = useState(false)

  const [password, setPassword] = useState('')
  const [rotateDegrees, setRotateDegrees] = useState(90)
  const [splitRanges, setSplitRanges] = useState('1-2')
  const [imageFormat, setImageFormat] = useState('png')
  const [ocrLanguage, setOcrLanguage] = useState('eng')

  const [watermarkText, setWatermarkText] = useState('CONFIDENTIAL')
  const [watermarkFontSize, setWatermarkFontSize] = useState('40')
  const [watermarkOpacity, setWatermarkOpacity] = useState('25')
  const [watermarkAngle, setWatermarkAngle] = useState('35')
  const [watermarkPosition, setWatermarkPosition] = useState('center')
  const [watermarkColor, setWatermarkColor] = useState('#777777')

  const {
    state,
    progress,
    jobId,
    results,
    kind,
    errorMessage,
    run,
    reset,
  } = useJobRunner()

  const active = OPERATIONS.find((item) => item.value === operation)!

  const needsPopup = [
    'split',
    'rotate',
    'protect',
    'unlock',
    'watermark',
    'to_images',
    'ocr',
  ].includes(operation)

  const accept = operation === 'from_images'
    ? '.jpg,.jpeg,.png,.webp,.avif,.gif,.bmp,.tiff,.tif,.ico,.heic,.heif,.svg'
    : '.pdf'

  const switchOperation = (next: Operation) => {
    setOperation(next)
    reset()
    setFiles([])
  }

  const buildFormData = (): FormData => {
    const form = new FormData()

    if (active.multiple) {
      files.forEach((file) => form.append('files', file))
    } else {
      form.append('file', files[0])
    }

    if (operation === 'protect' || operation === 'unlock') {
      form.append('password', password)
    }

    if (operation === 'rotate') {
      form.append('degrees', String(rotateDegrees))
    }

    if (operation === 'split') {
      form.append('ranges', JSON.stringify(parseRanges(splitRanges)))
    }

    if (operation === 'to_images') {
      form.append('image_format', imageFormat)
    }

    if (operation === 'ocr') {
      form.append('language', ocrLanguage.trim() || 'eng')
    }

    if (operation === 'watermark') {
      form.append('text', watermarkText)
      form.append('fontsize', watermarkFontSize)
      form.append('opacity', String(Number(watermarkOpacity) / 100))
      form.append('angle', watermarkAngle)
      form.append('position', watermarkPosition)
      form.append('color', JSON.stringify([
        parseInt(watermarkColor.slice(1, 3), 16),
        parseInt(watermarkColor.slice(3, 5), 16),
        parseInt(watermarkColor.slice(5, 7), 16),
      ]))
    }

    return form
  }

  const start = async () => {
    if (!files.length) return
    await run(ENDPOINTS[operation], buildFormData())
    setPopupOpen(false)
  }

  const handlePrimary = () => {
    if (!files.length) return
    if (needsPopup) {
      setPopupOpen(true)
      return
    }
    void start()
  }

  const isBusy = state === 'uploading' || state === 'processing'

  const popupTitle = {
    split: 'Split pages',
    rotate: 'Rotate pages',
    protect: 'Protect PDF',
    unlock: 'Unlock PDF',
    watermark: 'Watermark settings',
    to_images: 'PDF image output',
    ocr: 'OCR settings',
  }[operation as Exclude<Operation, 'merge' | 'from_images'>] ?? ''

  return (
    <PageShell
      title="PDF Tools"
      description="Merge, split, rotate, protect, watermark, OCR, and convert PDFs locally."
      icon={<FileType2 className="h-5 w-5" />}
    >
      <div className="grid grid-cols-3 gap-2.5 sm:grid-cols-5">
        {OPERATIONS.map((item) => (
          <PdfOperationTile
            key={item.value}
            label={item.label}
            icon={item.icon}
            active={operation === item.value}
            onClick={() => switchOperation(item.value)}
          />
        ))}
      </div>

      <div className="mt-7">
        {!files.length ? (
          <Dropzone
            onFiles={(incoming) => { reset(); setFiles(incoming) }}
            multiple={active.multiple}
            accept={accept}
            hint={active.multiple
              ? operation === 'merge'
                ? 'Select PDFs in merge order'
                : 'Select images to combine into one PDF'
              : 'Select one PDF'}
          />
        ) : (
          <div className="space-y-5">
            <div className="space-y-2">
              {files.map((file, index) => (
                <FileChip
                  key={`${file.name}-${index}`}
                  name={file.name}
                  sizeLabel={formatBytes(file.size)}
                  onRemove={state === 'idle' ? () => setFiles((prev) => prev.filter((_, i) => i !== index)) : undefined}
                />
              ))}
            </div>

            {state === 'idle' ? (
              <button
                type="button"
                onClick={handlePrimary}
                className="focus-ring w-full rounded-2xl bg-kiwi-flesh px-5 py-3.5 text-sm font-bold text-white transition hover:bg-kiwi-flesh-600"
              >
                Run {active.label}
              </button>
            ) : null}

            {isBusy ? (
              <ProgressPanel label={`Running ${active.label.toLowerCase()}…`} progress={progress} />
            ) : null}

            {state === 'done' && jobId ? (
              <ResultPanel
                jobId={jobId}
                results={results}
                kind={kind ?? operation}
                onReset={() => { reset(); setFiles([]) }}
              />
            ) : null}

            {state === 'failed' ? (
              <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-600">
                {errorMessage}
              </div>
            ) : null}
          </div>
        )}
      </div>

      <Popup
        open={popupOpen}
        onClose={() => setPopupOpen(false)}
        title={popupTitle}
        width="lg"
        footer={(
          <>
            <button
              type="button"
              onClick={() => setPopupOpen(false)}
              className="focus-ring rounded-xl border border-stone-200 px-4 py-2 text-sm font-semibold text-kiwi-ink/60"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => void start()}
              className="focus-ring rounded-xl bg-kiwi-flesh px-4 py-2 text-sm font-bold text-white"
            >
              Run
            </button>
          </>
        )}
      >
        {(operation === 'protect' || operation === 'unlock') ? (
          <TextField
            type="password"
            placeholder="Password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoFocus
          />
        ) : null}

        {operation === 'split' ? (
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-kiwi-ink/45">
              Page ranges
            </label>
            <TextField
              className="mt-2"
              value={splitRanges}
              onChange={(event) => setSplitRanges(event.target.value)}
              placeholder="1-3,5-7,9"
            />
            <p className="mt-2 text-xs text-kiwi-ink/45">
              Each range becomes a separate PDF and Kiwi returns one ZIP.
            </p>
          </div>
        ) : null}

        {operation === 'rotate' ? (
          <div className="flex gap-2">
            {[90, 180, 270].map((degree) => (
              <button
                key={degree}
                type="button"
                onClick={() => setRotateDegrees(degree)}
                className={`focus-ring flex-1 rounded-xl border px-3 py-2.5 text-sm font-bold ${rotateDegrees === degree ? 'border-kiwi-flesh bg-kiwi-flesh text-white' : 'border-stone-200 bg-white text-kiwi-ink/65'}`}
              >
                {degree}°
              </button>
            ))}
          </div>
        ) : null}

        {operation === 'to_images' ? (
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-kiwi-ink/45">
              Output format
            </label>
            <div className="mt-2 grid grid-cols-3 gap-2">
              {['png', 'jpg', 'webp'].map((format) => (
                <button
                  key={format}
                  type="button"
                  onClick={() => setImageFormat(format)}
                  className={`rounded-xl border px-3 py-2.5 text-sm font-bold uppercase ${imageFormat === format ? 'border-kiwi-flesh bg-kiwi-flesh text-white' : 'border-stone-200 bg-white text-kiwi-ink/65'}`}
                >
                  {format}
                </button>
              ))}
            </div>
            <p className="mt-2 text-xs text-kiwi-ink/45">Every page is returned inside one ZIP.</p>
          </div>
        ) : null}

        {operation === 'ocr' ? (
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-kiwi-ink/45">
              Tesseract language
            </label>
            <TextField
              className="mt-2"
              value={ocrLanguage}
              onChange={(event) => setOcrLanguage(event.target.value)}
              placeholder="eng"
            />
            <p className="mt-2 text-xs text-kiwi-ink/45">The language data must be installed in your local Tesseract installation.</p>
          </div>
        ) : null}

        {operation === 'watermark' ? (
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label className="text-xs font-bold uppercase tracking-wider text-kiwi-ink/45">Watermark text</label>
              <TextField
                className="mt-2"
                value={watermarkText}
                onChange={(event) => setWatermarkText(event.target.value)}
                placeholder="CONFIDENTIAL"
              />
            </div>

            <div>
              <label className="text-xs font-bold uppercase tracking-wider text-kiwi-ink/45">Font size</label>
              <TextField
                className="mt-2"
                type="number"
                min={8}
                max={200}
                value={watermarkFontSize}
                onChange={(event) => setWatermarkFontSize(event.target.value)}
              />
            </div>

            <div>
              <label className="text-xs font-bold uppercase tracking-wider text-kiwi-ink/45">Opacity %</label>
              <TextField
                className="mt-2"
                type="number"
                min={0}
                max={100}
                value={watermarkOpacity}
                onChange={(event) => setWatermarkOpacity(event.target.value)}
              />
            </div>

            <div>
              <label className="text-xs font-bold uppercase tracking-wider text-kiwi-ink/45">Angle °</label>
              <TextField
                className="mt-2"
                type="number"
                min={-180}
                max={180}
                value={watermarkAngle}
                onChange={(event) => setWatermarkAngle(event.target.value)}
              />
            </div>

            <div>
              <label className="text-xs font-bold uppercase tracking-wider text-kiwi-ink/45">Color</label>
              <TextField
                className="mt-2 h-11 p-1"
                type="color"
                value={watermarkColor}
                onChange={(event) => setWatermarkColor(event.target.value)}
              />
            </div>

            <div className="sm:col-span-2">
              <label className="text-xs font-bold uppercase tracking-wider text-kiwi-ink/45">Position</label>
              <select
                value={watermarkPosition}
                onChange={(event) => setWatermarkPosition(event.target.value)}
                className="focus-ring mt-2 w-full rounded-xl border border-stone-200 bg-white px-4 py-2.5 text-sm"
              >
                <option value="center">Center</option>
                <option value="top-left">Top left</option>
                <option value="top-right">Top right</option>
                <option value="bottom-left">Bottom left</option>
                <option value="bottom-right">Bottom right</option>
              </select>
            </div>
          </div>
        ) : null}
      </Popup>
    </PageShell>
  )
}
