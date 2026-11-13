import React, { useRef, useState, useEffect, useCallback } from 'react'
import { RotateCw, RefreshCw, Maximize2 } from 'lucide-react'

export interface Point2D {
  x: number
  y: number
}

interface CropEditorProps {
  imageSrc: string
  originalWidth: number
  originalHeight: number
  initialCorners?: [number, number][]
  onCornersChange: (corners: [number, number][]) => void
  onRotate?: () => void
}

export function CropEditor({
  imageSrc,
  originalWidth,
  originalHeight,
  initialCorners,
  onCornersChange,
  onRotate,
}: CropEditorProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [corners, setCorners] = useState<Point2D[]>([
    { x: 0, y: 0 },
    { x: originalWidth, y: 0 },
    { x: originalWidth, y: originalHeight },
    { x: 0, y: originalHeight },
  ])
  const [activeHandle, setActiveHandle] = useState<number | null>(null)
  const [containerSize, setContainerSize] = useState<{ width: number; height: number }>({
    width: 1,
    height: 1,
  })

  // Synchronize initial corners
  useEffect(() => {
    if (initialCorners && initialCorners.length === 4) {
      setCorners(initialCorners.map(([x, y]) => ({ x, y })))
    } else {
      setCorners([
        { x: originalWidth * 0.05, y: originalHeight * 0.05 },
        { x: originalWidth * 0.95, y: originalHeight * 0.05 },
        { x: originalWidth * 0.95, y: originalHeight * 0.95 },
        { x: originalWidth * 0.05, y: originalHeight * 0.95 },
      ])
    }
  }, [initialCorners, originalWidth, originalHeight])

  // Measure container layout
  const updateContainerDimensions = useCallback(() => {
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect()
      setContainerSize({ width: rect.width, height: rect.height })
    }
  }, [])

  useEffect(() => {
    updateContainerDimensions()
    window.addEventListener('resize', updateContainerDimensions)
    return () => window.removeEventListener('resize', updateContainerDimensions)
  }, [updateContainerDimensions])

  // Scale factors between image coordinates and DOM container
  const scale = Math.min(
    containerSize.width / Math.max(1, originalWidth),
    containerSize.height / Math.max(1, originalHeight),
  )

  const renderedW = originalWidth * scale
  const renderedH = originalHeight * scale
  const offsetX = (containerSize.width - renderedW) / 2
  const offsetY = (containerSize.height - renderedH) / 2

  // Transform image coords -> display coords
  const toDisplay = (pt: Point2D) => ({
    x: offsetX + pt.x * scale,
    y: offsetY + pt.y * scale,
  })

  // Transform display coords -> image coords
  const toImage = (dispX: number, dispY: number) => ({
    x: Math.max(0, Math.min(originalWidth, (dispX - offsetX) / scale)),
    y: Math.max(0, Math.min(originalHeight, (dispY - offsetY) / scale)),
  })

  const handlePointerDown = (index: number) => (e: React.PointerEvent) => {
    e.preventDefault()
    ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
    setActiveHandle(index)
  }

  const handlePointerMove = (e: React.PointerEvent) => {
    if (activeHandle === null || !containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    const dispX = e.clientX - rect.left
    const dispY = e.clientY - rect.top
    const imgPt = toImage(dispX, dispY)

    const updated = [...corners]
    updated[activeHandle] = imgPt
    setCorners(updated)
  }

  const handlePointerUp = (e: React.PointerEvent) => {
    if (activeHandle !== null) {
      try {
        ;(e.target as HTMLElement).releasePointerCapture(e.pointerId)
      } catch {
        // pointer capture fallback
      }
      setActiveHandle(null)
      onCornersChange(corners.map((p) => [p.x, p.y]))
    }
  }

  const handleResetFull = () => {
    const full: Point2D[] = [
      { x: 0, y: 0 },
      { x: originalWidth, y: 0 },
      { x: originalWidth, y: originalHeight },
      { x: 0, y: originalHeight },
    ]
    setCorners(full)
    onCornersChange(full.map((p) => [p.x, p.y]))
  }

  const displayCorners = corners.map(toDisplay)
  const polyPoints = displayCorners.map((p) => `${p.x},${p.y}`).join(' ')

  const cornerLabels = ['TL', 'TR', 'BR', 'BL']

  return (
    <div className="flex flex-col items-center w-full">
      {/* Top Action Bar */}
      <div className="flex items-center justify-between w-full max-w-xl px-2 py-2 mb-2 text-xs font-medium text-stone-600 dark:text-stone-300">
        <span>Drag corners to align boundary</span>
        <div className="flex items-center gap-2">
          {onRotate && (
            <button
              type="button"
              onClick={onRotate}
              className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-stone-100 hover:bg-stone-200 dark:bg-stone-800 dark:hover:bg-stone-700 transition"
              title="Rotate 90 degrees"
            >
              <RotateCw className="w-3.5 h-3.5 text-stone-600 dark:text-stone-300" />
              <span>Rotate</span>
            </button>
          )}
          <button
            type="button"
            onClick={handleResetFull}
            className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-stone-100 hover:bg-stone-200 dark:bg-stone-800 dark:hover:bg-stone-700 transition"
            title="Reset to full image"
          >
            <Maximize2 className="w-3.5 h-3.5 text-stone-600 dark:text-stone-300" />
            <span>Full Image</span>
          </button>
        </div>
      </div>

      {/* Crop Canvas Container */}
      <div
        ref={containerRef}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        className="relative flex items-center justify-center w-full max-w-2xl h-[420px] sm:h-[480px] bg-stone-900/95 rounded-2xl overflow-hidden shadow-inner border border-black/10 dark:border-white/10 touch-none select-none"
      >
        {/* Document Background Image */}
        <img
          src={imageSrc}
          alt="Document to scan"
          className="absolute object-contain max-w-full max-h-full pointer-events-none"
          style={{
            width: renderedW,
            height: renderedH,
            left: offsetX,
            top: offsetY,
          }}
          onLoad={updateContainerDimensions}
        />

        {/* SVG Perspective Crop Polygon & Handles */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none">
          {/* Shaded Mask Outside Polygon */}
          <defs>
            <mask id="crop-mask">
              <rect width="100%" height="100%" fill="white" />
              <polygon points={polyPoints} fill="black" />
            </mask>
          </defs>
          <rect width="100%" height="100%" fill="rgba(0, 0, 0, 0.45)" mask="url(#crop-mask)" />

          {/* Polygon Boundary Lines */}
          <polygon
            points={polyPoints}
            fill="rgba(34, 197, 94, 0.12)"
            stroke="#22c55e"
            strokeWidth="2.5"
            strokeLinejoin="round"
          />

          {/* Cross lines for geometric alignment guide */}
          <line
            x1={(displayCorners[0].x + displayCorners[3].x) / 2}
            y1={(displayCorners[0].y + displayCorners[3].y) / 2}
            x2={(displayCorners[1].x + displayCorners[2].x) / 2}
            y2={(displayCorners[1].y + displayCorners[2].y) / 2}
            stroke="rgba(34, 197, 94, 0.3)"
            strokeDasharray="4 4"
            strokeWidth="1.5"
          />
          <line
            x1={(displayCorners[0].x + displayCorners[1].x) / 2}
            y1={(displayCorners[0].y + displayCorners[1].y) / 2}
            x2={(displayCorners[3].x + displayCorners[2].x) / 2}
            y2={(displayCorners[3].y + displayCorners[2].y) / 2}
            stroke="rgba(34, 197, 94, 0.3)"
            strokeDasharray="4 4"
            strokeWidth="1.5"
          />
        </svg>

        {/* 4 Interactive Corner Handles */}
        {displayCorners.map((pt, idx) => (
          <div
            key={idx}
            onPointerDown={handlePointerDown(idx)}
            className={`absolute flex items-center justify-center -translate-x-1/2 -translate-y-1/2 rounded-full cursor-grab active:cursor-grabbing transition-transform ${
              activeHandle === idx
                ? 'scale-125 z-30 shadow-lg ring-4 ring-kiwi-lime/50'
                : 'hover:scale-110 z-20 shadow-md'
            }`}
            style={{
              left: `${pt.x}px`,
              top: `${pt.y}px`,
              width: '36px',
              height: '36px',
            }}
          >
            <div className="w-6 h-6 rounded-full bg-white dark:bg-stone-900 border-2 border-kiwi-flesh dark:border-kiwi-lime flex items-center justify-center shadow-xs">
              <span className="text-[9px] font-extrabold text-stone-900 dark:text-stone-100 select-none">
                {cornerLabels[idx]}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

