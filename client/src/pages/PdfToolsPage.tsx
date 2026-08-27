import { useState } from 'react'
import { PageShell } from '../components/layout/PageShell'
import { Dropzone } from '../components/features/Dropzone'
import { FileChip, formatBytes } from '../components/features/FileChip'
import { ProgressPanel } from '../components/features/ProgressPanel'
import { ResultPanel } from '../components/features/ResultPanel'
import { PdfOperationTile } from '../components/features/PdfOperationTile'
import { Popup } from '../components/ui/Popup'
import { TextField } from '../components/ui/TextField'
import {
  LayersIcon,
  ScissorsIcon,
  ImageStackIcon,
  RotateIcon,
  LockIcon,
  UnlockIcon,
  WatermarkIcon,
  ScanTextIcon,
  PdfIcon,
} from '../components/ui/icons'
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

const OPERATIONS: { value: Operation; label: string; icon: JSX.Element; multiple: boolean }[] = [
  { value: 'merge', label: 'Merge', icon: <LayersIcon className="h-5 w-5" />, multiple: true },
  { value: 'split', label: 'Split', icon: <ScissorsIcon className="h-5 w-5" />, multiple: false },
  { value: 'to_images', label: 'PDF → Images', icon: <ImageStackIcon className="h-5 w-5" />, multiple: false },
  { value: 'from_images', label: 'Images → PDF', icon: <ImageStackIcon className="h-5 w-5" />, multiple: true },
  { value: 'rotate', label: 'Rotate', icon: <RotateIcon className="h-5 w-5" />, multiple: false },
  { value: 'protect', label: 'Protect', icon: <LockIcon className="h-5 w-5" />, multiple: false },
  { value: 'unlock', label: 'Unlock', icon: <UnlockIcon className="h-5 w-5" />, multiple: false },
  { value: 'watermark', label: 'Watermark', icon: <WatermarkIcon className="h-5 w-5" />, multiple: false },
  { value: 'ocr', label: 'OCR', icon: <ScanTextIcon className="h-5 w-5" />, multiple: false },
]

const OPERATION_ENDPOINT: Record<Operation, string> = {
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

const NEEDS_PASSWORD_POPUP: Operation[] = ['protect', 'unlock']
const NEEDS_TEXT_POPUP: Operation[] = ['watermark']
const NEEDS_ROTATE_POPUP: Operation[] = ['rotate']

export default function PdfToolsPage() {
  const [operation, setOperation] = useState<Operation>('merge')
  const [files, setFiles] = useState<File[]>([])
  const [popupOpen, setPopupOpen] = useState(false)
  const [password, setPassword] = useState('')
  const [watermarkText, setWatermarkText] = useState('')
  const [rotateDegrees, setRotateDegrees] = useState(90)
  const { state, progress, jobId, fileCount, errorMessage, run, reset } = useJobRunner()

  const activeConfig = OPERATIONS.find((op) => op.value === operation)!

  const switchOperation = (op: Operation) => {
    setOperation(op)
    reset()
    setFiles([])
  }

  const handleFiles = (incoming: File[]) => {
    reset()
    setFiles(incoming)
  }

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const buildFormData = (): FormData => {
    const formData = new FormData()
    if (activeConfig.multiple) {
      files.forEach((f) => formData.append('files', f))
    } else {
      formData.append('file', files[0])
    }

    if (operation === 'protect' || operation === 'unlock') {
      formData.append('password', password)
    }
    if (operation === 'watermark') {
      formData.append('text', watermarkText)
    }
    if (operation === 'rotate') {
      formData.append('degrees', String(rotateDegrees))
    }
    if (operation === 'split') {
      formData.append('ranges', JSON.stringify([[1, 1]]))
    }
    return formData
  }

  const startRun = async () => {
    const formData = buildFormData()
    await run(OPERATION_ENDPOINT[operation], formData)
  }

  const handlePrimaryAction = () => {
    if (!files.length) return
    if (NEEDS_PASSWORD_POPUP.includes(operation) || NEEDS_TEXT_POPUP.includes(operation) || NEEDS_ROTATE_POPUP.includes(operation)) {
      setPopupOpen(true)
      return
    }
    startRun()
  }

  const confirmPopup = async () => {
    setPopupOpen(false)
    await startRun()
  }

  const isBusy = state === 'uploading' || state === 'processing'

  return (
    <PageShell
      title="PDF Tools"
      description="Merge, split, rotate, protect, watermark, OCR, and convert PDFs."
      icon={<PdfIcon className="h-5 w-5" />}
    >
      <div className="grid grid-cols-3 gap-2.5 sm:grid-cols-5">
        {OPERATIONS.map((op) => (
          <PdfOperationTile
            key={op.value}
            label={op.label}
            icon={op.icon}
            active={operation === op.value}
            onClick={() => switchOperation(op.value)}
          />
        ))}
      </div>

      <div className="mt-7">
        {!files.length ? (
          <Dropzone
            onFiles={handleFiles}
            multiple={activeConfig.multiple}
            accept={operation === 'from_images' ? 'image/*' : '.pdf'}
            hint={
              activeConfig.multiple
                ? operation === 'merge'
                  ? 'Drop two or more PDFs, in the order you want them merged'
                  : 'Drop the images you want combined into one PDF'
                : 'Drop a PDF file'
            }
          />
        ) : (
          <div className="space-y-5">
            <div className="space-y-2">
              {files.map((file, index) => (
                <FileChip
                  key={`${file.name}-${index}`}
                  name={file.name}
                  sizeLabel={formatBytes(file.size)}
                  onRemove={state === 'idle' ? () => removeFile(index) : undefined}
                />
              ))}
            </div>

            {state === 'idle' ? (
              <button
                type="button"
                onClick={handlePrimaryAction}
                className="focus-ring w-full rounded-xl bg-kiwi-flesh px-5 py-3 text-sm font-semibold text-white transition hover:bg-kiwi-flesh-600"
              >
                Run {activeConfig.label}
              </button>
            ) : null}

            {isBusy ? <ProgressPanel label={`Running ${activeConfig.label.toLowerCase()}…`} progress={progress} /> : null}

            {state === 'done' && jobId ? (
              <ResultPanel
                jobId={jobId}
                fileCount={fileCount}
                onReset={() => {
                  reset()
                  setFiles([])
                }}
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
        title={
          operation === 'protect'
            ? 'Set a password'
            : operation === 'unlock'
              ? 'Enter the password'
              : operation === 'rotate'
                ? 'Rotate pages'
                : 'Add watermark text'
        }
        footer={
          <>
            <button
              type="button"
              onClick={() => setPopupOpen(false)}
              className="focus-ring rounded-xl border border-kiwi-shell-50 px-4 py-2 text-sm font-medium text-kiwi-ink/60 transition hover:bg-kiwi-flesh-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={confirmPopup}
              className="focus-ring rounded-xl bg-kiwi-flesh px-4 py-2 text-sm font-semibold text-white transition hover:bg-kiwi-flesh-600"
            >
              Confirm
            </button>
          </>
        }
      >
        {(operation === 'protect' || operation === 'unlock') && (
          <TextField
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoFocus
          />
        )}
        {operation === 'watermark' && (
          <TextField
            type="text"
            placeholder="Watermark text"
            value={watermarkText}
            onChange={(e) => setWatermarkText(e.target.value)}
            autoFocus
          />
        )}
        {operation === 'rotate' && (
          <div className="flex gap-2">
            {[90, 180, 270].map((deg) => (
              <button
                key={deg}
                type="button"
                onClick={() => setRotateDegrees(deg)}
                className={`focus-ring flex-1 rounded-xl border px-3 py-2.5 text-sm font-semibold transition ${
                  rotateDegrees === deg
                    ? 'border-kiwi-flesh bg-kiwi-flesh text-white'
                    : 'border-kiwi-shell-50 bg-white text-kiwi-ink/70'
                }`}
              >
                {deg}°
              </button>
            ))}
          </div>
        )}
      </Popup>
    </PageShell>
  )
}
