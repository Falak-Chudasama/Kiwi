import React, { useState, useEffect } from 'react'
import {
  Camera,
  Upload,
  Plus,
  Trash2,
  RotateCw,
  FileText,
  Sliders,
  CheckCircle2,
  Sparkles,
  Download,
  AlertCircle,
  FileCheck,
} from 'lucide-react'
import { PageShell } from '../components/layout/PageShell'
import { CameraCapture } from '../components/features/CameraCapture'
import { CropEditor } from '../components/features/CropEditor'
import { ResultPanel } from '../components/features/ResultPanel'
import { CustomSelect, type SelectOption } from '../components/ui/CustomSelect'
import {
  detectDocument,
  fetchScannerPresets,
  type ScannerPreset,
  type DocumentDetectResponse,
} from '../lib/api'
import { useJobRunner } from '../hooks/useJobRunner'

interface ScannedPageItem {
  id: string
  file: File
  previewUrl: string
  originalWidth: number
  originalHeight: number
  corners: [number, number][]
  rotation: number
  detection?: DocumentDetectResponse
}

export default function ScannerPage() {
  const [pages, setPages] = useState<ScannedPageItem[]>([])
  const [activePageIndex, setActivePageIndex] = useState<number>(0)
  const [showCamera, setShowCamera] = useState<boolean>(false)
  const [presets, setPresets] = useState<ScannerPreset[]>([])
  const [selectedPresetId, setSelectedPresetId] = useState<string>('auto')
  const [showAdvancedSliders, setShowAdvancedSliders] = useState<boolean>(false)
  const [outputFormat, setOutputFormat] = useState<string>('pdf_searchable')

  // Manual adjustment slider overrides
  const [brightness, setBrightness] = useState<number>(0)
  const [contrast, setContrast] = useState<number>(0)
  const [whites, setWhites] = useState<number>(0)
  const [blacks, setBlacks] = useState<number>(0)
  const [sharpness, setSharpness] = useState<number>(0.3)
  const [dewarp, setDewarp] = useState<boolean>(false)

  const { state, progress, jobId, results, errorMessage, isBusy, run, reset } = useJobRunner()

  // Load presets on mount
  useEffect(() => {
    fetchScannerPresets()
      .then((data) => setPresets(data))
      .catch(() => {})
  }, [])

  // Ingest captured or uploaded file
  const handleIngestFile = async (file: File) => {
    const previewUrl = URL.createObjectURL(file)
    const img = new Image()
    img.src = previewUrl
    await new Promise((resolve) => {
      img.onload = resolve
    })

    const w = img.naturalWidth || 1200
    const h = img.naturalHeight || 1600

    const newPage: ScannedPageItem = {
      id: Math.random().toString(36).substring(2, 9),
      file,
      previewUrl,
      originalWidth: w,
      originalHeight: h,
      corners: [
        [w * 0.04, h * 0.04],
        [w * 0.96, h * 0.04],
        [w * 0.96, h * 0.96],
        [w * 0.04, h * 0.96],
      ],
      rotation: 0,
    }

    setPages((prev) => [...prev, newPage])
    setActivePageIndex(pages.length)
    setShowCamera(false)

    // Trigger backend CV detection for smart corner placement
    try {
      const detectResult = await detectDocument(file)
      setPages((prev) =>
        prev.map((p) =>
          p.id === newPage.id
            ? {
                ...p,
                corners: detectResult.corners,
                detection: detectResult,
              }
            : p,
        ),
      )
    } catch {
      // Fallback stays active
    }
  }

  const handleMultipleFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      Array.from(e.target.files).forEach(handleIngestFile)
    }
  }

  const handleRotateActive = () => {
    setPages((prev) =>
      prev.map((p, idx) =>
        idx === activePageIndex ? { ...p, rotation: (p.rotation + 90) % 360 } : p,
      ),
    )
  }

  const handleDeleteActive = () => {
    setPages((prev) => prev.filter((_, idx) => idx !== activePageIndex))
    setActivePageIndex((prev) => Math.max(0, prev - 1))
  }

  const handleCornersChange = (newCorners: [number, number][]) => {
    setPages((prev) =>
      prev.map((p, idx) => (idx === activePageIndex ? { ...p, corners: newCorners } : p)),
    )
  }

  const activePage = pages[activePageIndex]

  // Submit scan job
  const handleProcessScan = async () => {
    if (pages.length === 0) return

    const formData = new FormData()
    pages.forEach((p) => {
      formData.append('files', p.file)
    })

    const crops = pages.map((p) => p.corners)
    const rotations = pages.map((p) => p.rotation)
    formData.append('crops', JSON.stringify(crops))
    formData.append('rotations', JSON.stringify(rotations))
    formData.append('preset_id', selectedPresetId)
    formData.append('output_format', outputFormat)

    if (showAdvancedSliders) {
      const customSettings = {
        brightness,
        contrast,
        whites,
        blacks,
        sharpen: sharpness,
        dewarp_enabled: dewarp,
      }
      formData.append('custom_settings', JSON.stringify(customSettings))
    }

    await run('/api/v1/scanner/jobs', formData)
  }

  return (
    <PageShell
      title="Scanner"
      description="Quiet, offline document digitization with perspective rectification and OCR."
      icon={<Camera className="h-4 w-4" />}
    >
      <div className="flex flex-col gap-6 max-w-4xl mx-auto">
        {/* Camera Modal View */}
        {showCamera && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
            <CameraCapture
              onCapture={handleIngestFile}
              onCancel={() => setShowCamera(false)}
            />
          </div>
        )}

        {/* State: Done with output */}
        {state === 'done' && jobId && results.length > 0 ? (
          <ResultPanel
            jobId={jobId}
            results={results}
            kind="scanner_process"
            onReset={() => {
              reset()
              setPages([])
            }}
          />
        ) : pages.length === 0 ? (
          /* State 1: Capture or Import Dropzone */
          <div className="flex flex-col items-center justify-center p-12 border-2 border-dashed border-stone-300 dark:border-stone-700 rounded-3xl bg-white/50 dark:bg-stone-900/30 text-center gap-5 transition">
            <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-kiwi-flesh/10 dark:bg-kiwi-lime/10 text-kiwi-flesh dark:text-kiwi-lime">
              <Camera className="w-8 h-8" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-stone-900 dark:text-white">
                Scan or Import Document
              </h2>
              <p className="text-xs text-stone-500 dark:text-stone-400 mt-1 max-w-sm">
                Capture paperwork using your camera or import existing photos and PDFs.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={() => setShowCamera(true)}
                className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-stone-900 text-white dark:bg-white dark:text-stone-900 font-bold text-sm shadow-xs hover:opacity-90 transition"
              >
                <Camera className="w-4 h-4" />
                <span>Open Camera</span>
              </button>

              <label className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-stone-100 dark:bg-stone-800 hover:bg-stone-200 dark:hover:bg-stone-700 text-stone-800 dark:text-stone-200 font-semibold text-sm cursor-pointer transition">
                <Upload className="w-4 h-4" />
                <span>Import Images or PDF</span>
                <input
                  type="file"
                  multiple
                  accept="image/*,application/pdf"
                  onChange={handleMultipleFiles}
                  className="hidden"
                />
              </label>
            </div>
          </div>
        ) : (
          /* State 2: Review, Crop, Preset & Export Workspace */
          <div className="flex flex-col gap-6">
            {/* Top Toolbar: Thumbnails & Page Controls */}
            <div className="glass-panel flex items-center justify-between p-3 rounded-2xl shadow-xs">
              <div className="flex items-center gap-2 overflow-x-auto py-1 max-w-lg">
                {pages.map((p, idx) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => setActivePageIndex(idx)}
                    className={`relative shrink-0 w-14 h-16 rounded-lg overflow-hidden border-2 transition ${
                      idx === activePageIndex
                        ? 'border-kiwi-flesh dark:border-kiwi-lime ring-2 ring-kiwi-lime/30'
                        : 'border-transparent opacity-70 hover:opacity-100'
                    }`}
                  >
                    <img src={p.previewUrl} alt={`Page ${idx + 1}`} className="w-full h-full object-cover" />
                    <span className="absolute bottom-0 inset-x-0 bg-black/60 text-[9px] font-bold text-white text-center py-0.5">
                      {idx + 1}
                    </span>
                  </button>
                ))}

                <button
                  type="button"
                  onClick={() => setShowCamera(true)}
                  className="flex flex-col items-center justify-center shrink-0 w-14 h-16 rounded-lg border border-dashed border-stone-300 dark:border-stone-700 hover:bg-stone-100 dark:hover:bg-stone-800 text-stone-500 transition"
                  title="Add page with camera"
                >
                  <Plus className="w-4 h-4" />
                  <span className="text-[9px] font-semibold mt-0.5">Add</span>
                </button>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleRotateActive}
                  className="p-2 rounded-lg text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 transition"
                  title="Rotate page"
                >
                  <RotateCw className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={handleDeleteActive}
                  className="p-2 rounded-lg text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition"
                  title="Delete page"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Quality Assessment Banner */}
            {activePage?.detection?.quality && (
              <div className="flex items-center gap-3 px-4 py-2.5 rounded-xl bg-kiwi-flesh/5 dark:bg-kiwi-lime/5 border border-kiwi-flesh/20 dark:border-kiwi-lime/20 text-xs">
                <Sparkles className="w-4 h-4 text-kiwi-flesh dark:text-kiwi-lime shrink-0" />
                <span className="text-stone-700 dark:text-stone-300">
                  {activePage.detection.quality.suggestions[0] || 'Good quality capture.'}
                </span>
              </div>
            )}

            {/* Interactive 4-Corner Crop Editor */}
            {activePage && (
              <CropEditor
                imageSrc={activePage.previewUrl}
                originalWidth={activePage.originalWidth}
                originalHeight={activePage.originalHeight}
                initialCorners={activePage.corners}
                onCornersChange={handleCornersChange}
                onRotate={handleRotateActive}
              />
            )}

            {/* Presets Row */}
            <div className="glass-panel flex flex-col gap-2 p-4 rounded-2xl">
              <div className="flex items-center justify-between text-xs font-bold text-stone-500 dark:text-stone-400">
                <span>ENHANCEMENT PRESET</span>
                <button
                  type="button"
                  onClick={() => setShowAdvancedSliders(!showAdvancedSliders)}
                  className="flex items-center gap-1 text-kiwi-flesh dark:text-kiwi-lime hover:underline"
                >
                  <Sliders className="w-3.5 h-3.5" />
                  <span>{showAdvancedSliders ? 'Hide Sliders' : 'Fine-Tune'}</span>
                </button>
              </div>

              {/* Horizontal Pill Row */}
              <div className="grid grid-cols-2 sm:grid-cols-6 gap-2 pt-1">
                {presets.map((preset) => (
                  <button
                    key={preset.id}
                    type="button"
                    onClick={() => setSelectedPresetId(preset.id)}
                    className={`px-3 py-2 rounded-xl text-xs font-semibold text-center transition ${
                      selectedPresetId === preset.id
                        ? 'bg-stone-900 text-white dark:bg-white dark:text-stone-900 shadow-xs'
                        : 'bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-300 hover:bg-stone-200 dark:hover:bg-stone-700'
                    }`}
                  >
                    {preset.name}
                  </button>
                ))}
              </div>

              {/* Progressive Disclosure: Manual Adjustment Sliders */}
              {showAdvancedSliders && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 mt-2 border-t border-stone-200 dark:border-stone-800 text-xs">
                  <div>
                    <div className="flex justify-between text-stone-600 dark:text-stone-300 mb-1">
                      <span>Brightness</span>
                      <span>{brightness}</span>
                    </div>
                    <input
                      type="range"
                      min="-50"
                      max="50"
                      value={brightness}
                      onChange={(e) => setBrightness(Number(e.target.value))}
                      className="w-full accent-kiwi-flesh dark:accent-kiwi-lime"
                    />
                  </div>
                  <div>
                    <div className="flex justify-between text-stone-600 dark:text-stone-300 mb-1">
                      <span>Contrast</span>
                      <span>{contrast}</span>
                    </div>
                    <input
                      type="range"
                      min="-50"
                      max="50"
                      value={contrast}
                      onChange={(e) => setContrast(Number(e.target.value))}
                      className="w-full accent-kiwi-flesh dark:accent-kiwi-lime"
                    />
                  </div>
                  <div>
                    <div className="flex justify-between text-stone-600 dark:text-stone-300 mb-1">
                      <span>Paper Whitening</span>
                      <span>{whites}</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="80"
                      value={whites}
                      onChange={(e) => setWhites(Number(e.target.value))}
                      className="w-full accent-kiwi-flesh dark:accent-kiwi-lime"
                    />
                  </div>
                  <div>
                    <div className="flex justify-between text-stone-600 dark:text-stone-300 mb-1">
                      <span>Text Sharpness</span>
                      <span>{Math.round(sharpness * 100)}%</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={sharpness}
                      onChange={(e) => setSharpness(Number(e.target.value))}
                      className="w-full accent-kiwi-flesh dark:accent-kiwi-lime"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Export Format Selector & Primary Action */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-3xl bg-white/70 dark:bg-[#181915]/70 backdrop-blur-xl border border-black/[0.06] dark:border-white/[0.08] shadow-sm">
              <div className="flex-1 max-w-sm">
                <CustomSelect
                  label="Output Format"
                  value={outputFormat}
                  onChange={(val) => setOutputFormat(val)}
                  options={[
                    { value: 'pdf_searchable', label: 'Searchable PDF (with OCR)', sublabel: 'Embedded text layer for full searching' },
                    { value: 'pdf_image', label: 'Image-only PDF', sublabel: 'Crisp page layout without text layer' },
                    { value: 'images_zip', label: 'Enhanced Images (.zip)', sublabel: 'Archive of perspective-corrected images' },
                    { value: 'txt', label: 'Extracted Text (.txt)', sublabel: 'Plain text OCR transcript' },
                  ]}
                />
              </div>

              <button
                type="button"
                onClick={handleProcessScan}
                disabled={isBusy}
                className="btn-glass-primary w-full sm:w-auto"
              >
                {isBusy ? `Scanning (${progress}%)...` : `Scan ${pages.length} Page${pages.length > 1 ? 's' : ''}`}
              </button>
            </div>

            {/* Error Display */}
            {errorMessage && (
              <div className="p-4 rounded-2xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </PageShell>
  )
}

