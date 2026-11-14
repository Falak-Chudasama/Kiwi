import { useState } from 'react'
import {
  ArrowDownUp,
  FileText,
  Image as ImageIcon,
  Layers3,
  Lock,
  RotateCw,
  ScanText,
  Scissors,
  Stamp,
  Unlock,
  AlertCircle,
} from 'lucide-react'

import { PageShell } from '../components/layout/PageShell'
import { Dropzone } from '../components/features/Dropzone'
import { FileChip, formatBytes } from '../components/features/FileChip'
import { ProgressPanel } from '../components/features/ProgressPanel'
import { ResultPanel } from '../components/features/ResultPanel'
import { TextField } from '../components/ui/TextField'
import { CustomSelect } from '../components/ui/CustomSelect'
import { useJobRunner } from '../hooks/useJobRunner'

type Operation =
  | 'merge'
  | 'split'
  | 'reorder'
  | 'to_images'
  | 'from_images'
  | 'rotate'
  | 'protect'
  | 'unlock'
  | 'watermark'
  | 'ocr'

interface OperationDef {
  value: Operation
  label: string
  icon: typeof FileText
  multiple: boolean
  description: string
}

const OPERATIONS: OperationDef[] = [
  { value: 'merge', label: 'Merge', icon: Layers3, multiple: true, description: 'Combine multiple PDFs into a single document' },
  { value: 'split', label: 'Split', icon: Scissors, multiple: false, description: 'Extract page ranges into separate PDF documents' },
  { value: 'reorder', label: 'Reorder', icon: ArrowDownUp, multiple: false, description: 'Rearrange pages into a custom order' },
  { value: 'to_images', label: 'PDF to Images', icon: ImageIcon, multiple: false, description: 'Render PDF pages into high-resolution images' },
  { value: 'from_images', label: 'Images to PDF', icon: ImageIcon, multiple: true, description: 'Assemble image files into a single PDF' },
  { value: 'rotate', label: 'Rotate', icon: RotateCw, multiple: false, description: 'Rotate pages by 90°, 180°, or 270°' },
  { value: 'protect', label: 'Protect', icon: Lock, multiple: false, description: 'Encrypt a PDF with AES-256 password protection' },
  { value: 'unlock', label: 'Unlock', icon: Unlock, multiple: false, description: 'Remove password restriction from an encrypted PDF' },
  { value: 'watermark', label: 'Watermark', icon: Stamp, multiple: false, description: 'Overlay customized text across pages' },
  { value: 'ocr', label: 'OCR', icon: ScanText, multiple: false, description: 'Recognize text on scanned pages with Tesseract' },
]

function parseRanges(value: string): number[][] {
  const parts = value.split(',').map((item) => item.trim()).filter(Boolean)
  if (!parts.length) {
    throw new Error('Enter at least one page or range (e.g. 1-3, 5-7).')
  }

  return parts.map((item) => {
    if (item.includes('-')) {
      const [startStr, endStr] = item.split('-').map((s) => s.trim())
      const start = Number(startStr)
      const end = Number(endStr)
      if (!Number.isInteger(start) || !Number.isInteger(end) || start < 1 || end < start) {
        throw new Error(`Invalid range '${item}'. Example valid format: 1-3, 5-7.`)
      }
      return [start, end]
    }
    const page = Number(item)
    if (!Number.isInteger(page) || page < 1) {
      throw new Error(`Invalid page number '${item}'.`)
    }
    return [page, page]
  })
}

function parseOrder(value: string): number[] {
  const parts = value.split(',').map((s) => s.trim()).filter(Boolean)
  if (!parts.length) {
    throw new Error('Enter the 1-based page order (e.g. 3, 1, 2).')
  }
  const pages = parts.map((p) => {
    const num = Number(p)
    if (!Number.isInteger(num) || num < 1) {
      throw new Error(`Invalid page number '${p}'.`)
    }
    // Return 0-based index for backend
    return num - 1
  })
  return pages
}

export default function PdfToolsPage() {
  const [operation, setOperation] = useState<Operation>('merge')
  const [files, setFiles] = useState<File[]>([])

  // Options state
  const [password, setPassword] = useState('')
  const [rotateDegrees, setRotateDegrees] = useState(90)
  const [splitRanges, setSplitRanges] = useState('1-2')
  const [pageOrder, setPageOrder] = useState('2, 1')
  const [imageFormat, setImageFormat] = useState('png')
  const [dpi, setDpi] = useState(150)
  const [watermarkText, setWatermarkText] = useState('CONFIDENTIAL')
  const [watermarkOpacity, setWatermarkOpacity] = useState(0.25)
  const [watermarkSize, setWatermarkSize] = useState(40)
  const [watermarkAngle, setWatermarkAngle] = useState(35)
  const [ocrLanguage, setOcrLanguage] = useState('eng')

  const { state, progress, jobId, results, kind, errorMessage, isBusy, run, cancel, reset } =
    useJobRunner()

  const currentOp = OPERATIONS.find((op) => op.value === operation)!

  const switchOperation = (next: Operation) => {
    setOperation(next)
    reset()
    setFiles([])
  }

  const handleFiles = (incoming: File[]) => {
    reset()
    setFiles(incoming)
  }

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
    reset()
  }

  const handleSubmit = async () => {
    if (!files.length) return
    const formData = new FormData()

    try {
      if (operation === 'merge') {
        files.forEach((f) => formData.append('files', f))
        await run('/api/pdf/merge', formData)
      } else if (operation === 'split') {
        const ranges = parseRanges(splitRanges)
        formData.append('file', files[0])
        formData.append('ranges', JSON.stringify(ranges))
        await run('/api/pdf/split', formData)
      } else if (operation === 'reorder') {
        const order = parseOrder(pageOrder)
        formData.append('file', files[0])
        formData.append('order', JSON.stringify(order))
        await run('/api/pdf/reorder', formData)
      } else if (operation === 'to_images') {
        formData.append('file', files[0])
        formData.append('image_format', imageFormat)
        formData.append('dpi', String(dpi))
        await run('/api/pdf/to-images', formData)
      } else if (operation === 'from_images') {
        files.forEach((f) => formData.append('files', f))
        await run('/api/pdf/from-images', formData)
      } else if (operation === 'rotate') {
        formData.append('file', files[0])
        formData.append('degrees', String(rotateDegrees))
        await run('/api/pdf/rotate', formData)
      } else if (operation === 'protect') {
        if (!password.trim()) throw new Error('Password cannot be empty.')
        formData.append('file', files[0])
        formData.append('password', password)
        await run('/api/pdf/protect', formData)
      } else if (operation === 'unlock') {
        if (!password.trim()) throw new Error('Password cannot be empty.')
        formData.append('file', files[0])
        formData.append('password', password)
        await run('/api/pdf/unlock', formData)
      } else if (operation === 'watermark') {
        if (!watermarkText.trim()) throw new Error('Watermark text cannot be empty.')
        formData.append('file', files[0])
        formData.append('text', watermarkText)
        formData.append('fontsize', String(watermarkSize))
        formData.append('opacity', String(watermarkOpacity))
        formData.append('angle', String(watermarkAngle))
        formData.append('color', '120,120,120')
        await run('/api/pdf/watermark', formData)
      } else if (operation === 'ocr') {
        formData.append('file', files[0])
        formData.append('language', ocrLanguage)
        await run('/api/pdf/ocr', formData)
      }
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Invalid parameters.')
    }
  }

  const acceptPattern = operation === 'from_images' ? '.png,.jpg,.jpeg,.webp,.avif,.tiff' : '.pdf'

  return (
    <PageShell
      title="PDF Workspace"
      description="Merge, split, reorder, render, protect, watermark, and OCR PDF documents."
      icon={<FileText className="h-4 w-4" />}
    >
      {/* Operation Tabs Strip */}
      <div className="glass-panel flex flex-wrap gap-2 rounded-2xl p-2 shadow-soft">
        {OPERATIONS.map(({ value, label, icon: Icon }) => (
          <button
            key={value}
            type="button"
            onClick={() => switchOperation(value)}
            className={`flex items-center gap-2 rounded-xl px-3.5 py-2.5 text-xs sm:text-sm font-semibold transition ${
              operation === value
                ? 'bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-xs'
                : 'text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 hover:text-stone-900 dark:hover:text-white'
            }`}
          >
            <Icon className="h-4 w-4" />
            <span>{label}</span>
          </button>
        ))}
      </div>

      {!files.length ? (
        <Dropzone
          onFiles={handleFiles}
          multiple={currentOp.multiple}
          accept={acceptPattern}
          hint={
            operation === 'from_images'
              ? 'Select images to assemble into a PDF'
              : `${currentOp.description} (${currentOp.multiple ? 'select multiple PDFs' : 'select one PDF'})`
          }
        />
      ) : (
        <div className="space-y-6">
          {/* Selected File(s) */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold uppercase tracking-wider text-stone-500 dark:text-stone-400">
                Selected Input ({files.length})
              </span>
              {state === 'idle' && (
                <button
                  type="button"
                  onClick={() => {
                    reset()
                    setFiles([])
                  }}
                  className="text-sm font-semibold text-stone-400 dark:text-stone-500 hover:text-stone-700 dark:hover:text-stone-300 transition"
                >
                  Clear all
                </button>
              )}
            </div>
            {files.map((file, idx) => (
              <FileChip
                key={`${file.name}-${idx}`}
                name={file.name}
                sizeLabel={formatBytes(file.size)}
                onRemove={state === 'idle' ? () => removeFile(idx) : undefined}
              />
            ))}
          </div>

          {/* Contextual Operation Configuration */}
          {state === 'idle' && (
            <div className="glass-panel rounded-2xl p-6 shadow-soft space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-stone-500 dark:text-stone-400">
                {currentOp.label} Options
              </h2>

              {operation === 'split' && (
                <div className="space-y-2 text-xs">
                  <label className="block font-semibold text-stone-700 dark:text-stone-300">
                    Page Ranges to Extract
                  </label>
                  <TextField
                    placeholder="e.g. 1-2, 3-5, 8"
                    value={splitRanges}
                    onChange={(e) => setSplitRanges(e.target.value)}
                  />
                  <p className="text-[11px] text-stone-400 dark:text-stone-500">
                    Each range is extracted as a separate result file available for individual or batch download.
                  </p>
                </div>
              )}

              {operation === 'reorder' && (
                <div className="space-y-2 text-xs">
                  <label className="block font-semibold text-stone-700 dark:text-stone-300">
                    New Page Sequence (1-based page numbers)
                  </label>
                  <TextField
                    placeholder="e.g. 3, 1, 2"
                    value={pageOrder}
                    onChange={(e) => setPageOrder(e.target.value)}
                  />
                  <p className="text-[11px] text-stone-400 dark:text-stone-500">
                    Specify the desired page order. Every page from the original document must appear exactly once.
                  </p>
                </div>
              )}

              {operation === 'to_images' && (
                <div className="grid gap-3 sm:grid-cols-2 text-xs">
                  <div>
                    <CustomSelect
                      label="Image Format"
                      value={imageFormat}
                      onChange={setImageFormat}
                      options={[
                        { value: 'png', label: 'PNG (Lossless)', sublabel: 'High-detail graphics' },
                        { value: 'jpg', label: 'JPG (Photo/Document)', sublabel: 'Standard compressed' },
                        { value: 'webp', label: 'WebP (Efficient)', sublabel: 'Modern web format' },
                        { value: 'tiff', label: 'TIFF (Archive)', sublabel: 'Uncompressed archival' },
                        { value: 'bmp', label: 'BMP (Raw)', sublabel: 'Uncompressed bitmap' },
                      ]}
                    />
                  </div>
                  <div>
                    <CustomSelect
                      label="Render Quality (DPI)"
                      value={dpi}
                      onChange={(val) => setDpi(Number(val))}
                      options={[
                        { value: 96, label: '96 DPI (Web Draft)', sublabel: 'Fastest rasterization' },
                        { value: 150, label: '150 DPI (Balanced Standard)', sublabel: 'Recommended default' },
                        { value: 300, label: '300 DPI (High Resolution Print)', sublabel: 'Maximum crispness' },
                      ]}
                    />
                  </div>
                </div>
              )}

              {operation === 'rotate' && (
                <div className="space-y-2 text-xs">
                  <label className="block font-semibold text-stone-700 dark:text-stone-300">Rotation Angle</label>
                  <div className="flex gap-2">
                    {[90, 180, 270].map((deg) => (
                      <button
                        key={deg}
                        type="button"
                        onClick={() => setRotateDegrees(deg)}
                        className={`rounded-xl px-4 py-2 text-xs font-bold transition border ${
                          rotateDegrees === deg
                            ? 'bg-stone-900 text-white border-stone-900 dark:bg-stone-100 dark:text-stone-900 dark:border-stone-100'
                            : 'glass-card text-stone-700 dark:text-stone-300 hover:bg-white/40 dark:hover:bg-white/[0.05]'
                        }`}
                      >
                        +{deg}° Clockwise
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {(operation === 'protect' || operation === 'unlock') && (
                <div className="space-y-2 text-xs">
                  <label className="block font-semibold text-stone-700 dark:text-stone-300">
                    {operation === 'protect' ? 'Set Password for PDF' : 'Document Password'}
                  </label>
                  <TextField
                    type="password"
                    placeholder="Enter password..."
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                  <p className="text-[11px] text-stone-400 dark:text-stone-500">
                    {operation === 'protect'
                      ? 'Applies AES-256 standard encryption.'
                      : 'Decryption happens locally in process RAM.'}
                  </p>
                </div>
              )}

              {operation === 'watermark' && (
                <div className="space-y-3 text-xs">
                  <div>
                    <label className="block font-semibold text-stone-700 dark:text-stone-300 mb-1">Watermark Text</label>
                    <TextField
                      value={watermarkText}
                      onChange={(e) => setWatermarkText(e.target.value)}
                      placeholder="e.g. CONFIDENTIAL"
                    />
                  </div>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <div>
                      <label className="block font-semibold text-stone-700 dark:text-stone-300 mb-1">
                        Opacity ({Math.round(watermarkOpacity * 100)}%)
                      </label>
                      <input
                        type="range"
                        min="0.05"
                        max="1.0"
                        step="0.05"
                        value={watermarkOpacity}
                        onChange={(e) => setWatermarkOpacity(Number(e.target.value))}
                        className="w-full accent-kiwi-flesh"
                      />
                    </div>
                    <div>
                      <label className="block font-semibold text-stone-700 dark:text-stone-300 mb-1">
                        Font Size ({watermarkSize} pt)
                      </label>
                      <TextField
                        type="number"
                        min="10"
                        max="160"
                        value={watermarkSize}
                        onChange={(e) => setWatermarkSize(Number(e.target.value))}
                      />
                    </div>
                    <div>
                      <label className="block font-semibold text-stone-700 dark:text-stone-300 mb-1">
                        Angle ({watermarkAngle}°)
                      </label>
                      <TextField
                        type="number"
                        min="-90"
                        max="90"
                        value={watermarkAngle}
                        onChange={(e) => setWatermarkAngle(Number(e.target.value))}
                      />
                    </div>
                  </div>
                </div>
              )}

              {operation === 'ocr' && (
                <div className="space-y-2 text-xs">
                  <CustomSelect
                    label="OCR Language"
                    value={ocrLanguage}
                    onChange={setOcrLanguage}
                    options={[
                      { value: 'eng', label: 'English (eng)', sublabel: 'English alphabet and numerals' },
                      { value: 'deu', label: 'German (deu)', sublabel: 'German umlauts and standard text' },
                      { value: 'fra', label: 'French (fra)', sublabel: 'French accents and standard text' },
                      { value: 'spa', label: 'Spanish (spa)', sublabel: 'Spanish tildes and punctuation' },
                      { value: 'ita', label: 'Italian (ita)', sublabel: 'Italian standard text' },
                    ]}
                  />
                  <p className="text-[11px] text-stone-400 dark:text-stone-500">
                    Tesseract recognizes text on scanned pages and inserts an invisible searchable text layer over each page.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Action Trigger */}
          {state === 'idle' && (
            <div className="flex justify-end">
              <button
                type="button"
                onClick={handleSubmit}
                disabled={isBusy}
                className="btn-glass-primary w-full sm:w-auto"
              >
                <span>Execute {currentOp.label}</span>
              </button>
            </div>
          )}

          {/* Progress */}
          {isBusy && (
            <ProgressPanel
              label={`Processing PDF ${currentOp.label}…`}
              progress={progress}
              onCancel={cancel}
            />
          )}

          {/* Results */}
          {state === 'done' && jobId && (
            <ResultPanel
              jobId={jobId}
              results={results}
              kind={kind ?? 'pdf_tool'}
              onReset={() => {
                reset()
                setFiles([])
              }}
            />
          )}

          {/* Error Message */}
          {state === 'failed' && (
            <div className="flex items-start gap-3 rounded-2xl border border-rose-100 dark:border-rose-900/50 bg-rose-50/80 dark:bg-rose-950/40 p-4 text-xs text-rose-700 dark:text-rose-300 animate-slide-up">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-semibold">Operation failed</p>
                <p className="mt-1 text-rose-600 dark:text-rose-400">{errorMessage}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </PageShell>
  )
}
