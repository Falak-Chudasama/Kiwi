import React, { useRef, useState, useEffect, useCallback } from 'react'
import { Camera, FlipHorizontal, Zap, ZapOff, X, AlertCircle, CheckCircle2 } from 'lucide-react'

interface CameraCaptureProps {
  onCapture: (capturedFile: File) => void
  onCancel: () => void
}

export function CameraCapture({ onCapture, onCancel }: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [facingMode, setFacingMode] = useState<'environment' | 'user'>('environment')
  const [torchOn, setTorchOn] = useState<boolean>(false)
  const [hasTorch, setHasTorch] = useState<boolean>(false)
  const [isCapturing, setIsCapturing] = useState<boolean>(false)
  const [cameraError, setCameraError] = useState<string | null>(null)
  const [stabilityFeedback, setStabilityFeedback] = useState<string>('Aligning document...')
  const [isStable, setIsStable] = useState<boolean>(false)

  // Start camera stream
  const startCamera = useCallback(async (facing: 'environment' | 'user') => {
    try {
      setCameraError(null)
      if (stream) {
        stream.getTracks().forEach((track) => track.stop())
      }

      const constraints: MediaStreamConstraints = {
        audio: false,
        video: {
          facingMode: { ideal: facing },
          width: { ideal: 3840, min: 1280 },
          height: { ideal: 2160, min: 720 },
        },
      }

      const mediaStream = await navigator.mediaDevices.getUserMedia(constraints)
      setStream(mediaStream)

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream
        await videoRef.current.play()
      }

      // Check track capabilities for torch
      const videoTrack = mediaStream.getVideoTracks()[0]
      if (videoTrack) {
        const capabilities = videoTrack.getCapabilities ? (videoTrack.getCapabilities() as any) : {}
        setHasTorch(Boolean(capabilities?.torch))
      }
    } catch (err: any) {
      setCameraError(err.message || 'Unable to access camera. Please verify permissions.')
    }
  }, [stream])

  useEffect(() => {
    startCamera(facingMode)
    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop())
      }
    }
  }, [facingMode])

  // Toggle Torch/Flash
  const toggleTorch = async () => {
    if (!stream || !hasTorch) return
    const track = stream.getVideoTracks()[0]
    if (track && track.applyConstraints) {
      try {
        const nextTorch = !torchOn
        await track.applyConstraints({
          advanced: [{ torch: nextTorch } as any],
        })
        setTorchOn(nextTorch)
      } catch {
        // Torch constraint not permitted
      }
    }
  }

  // Camera switcher
  const switchCamera = () => {
    setFacingMode((prev) => (prev === 'environment' ? 'user' : 'environment'))
  }

  // Live frame analyzer for sharpness/stability assessment
  useEffect(() => {
    let animId: number
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    let lastLuma = 0

    const analyzeFrame = () => {
      if (videoRef.current && videoRef.current.readyState === 4 && ctx) {
        const video = videoRef.current
        canvas.width = 160
        canvas.height = 120
        ctx.drawImage(video, 0, 0, 160, 120)
        const frameData = ctx.getImageData(0, 0, 160, 120)
        const data = frameData.data

        // Compute mean luminance and frame-to-frame diff for motion stability
        let lumaSum = 0
        for (let i = 0; i < data.length; i += 4) {
          lumaSum += 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2]
        }
        const meanLuma = lumaSum / (data.length / 4)
        const motionDiff = Math.abs(meanLuma - lastLuma)
        lastLuma = meanLuma

        if (motionDiff < 1.2) {
          setIsStable(true)
          setStabilityFeedback('Document steady — ready to capture')
        } else {
          setIsStable(false)
          setStabilityFeedback('Hold steady for sharpest scan')
        }
      }
      animId = requestAnimationFrame(analyzeFrame)
    }

    animId = requestAnimationFrame(analyzeFrame)
    return () => cancelAnimationFrame(animId)
  }, [])

  // Shutter trigger (ImageCapture.takePhoto or canvas capture)
  const takePicture = async () => {
    if (!stream || isCapturing) return
    setIsCapturing(true)

    try {
      const track = stream.getVideoTracks()[0]

      // Try native ImageCapture API first for full-sensor still resolution
      if ('ImageCapture' in window) {
        try {
          const imageCapture = new (window as any).ImageCapture(track)
          const blob: Blob = await imageCapture.takePhoto()
          const file = new File([blob], `scan_${Date.now()}.jpg`, { type: 'image/jpeg' })
          onCapture(file)
          return
        } catch {
          // Fall back to video canvas capture
        }
      }

      // Canvas fallback
      if (videoRef.current) {
        const video = videoRef.current
        const canvas = document.createElement('canvas')
        canvas.width = video.videoWidth || 1920
        canvas.height = video.videoHeight || 1080
        const ctx = canvas.getContext('2d')
        if (ctx) {
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
          canvas.toBlob(
            (blob) => {
              if (blob) {
                const file = new File([blob], `scan_${Date.now()}.jpg`, { type: 'image/jpeg' })
                onCapture(file)
              }
            },
            'image/jpeg',
            0.95,
          )
        }
      }
    } finally {
      setIsCapturing(false)
    }
  }

  return (
    <div className="relative flex flex-col items-center justify-center w-full max-w-2xl bg-black rounded-3xl overflow-hidden shadow-2xl p-4">
      {/* Top Overlay Controls */}
      <div className="absolute top-6 inset-x-6 z-20 flex items-center justify-between text-white">
        <button
          type="button"
          onClick={onCancel}
          className="flex items-center justify-center w-10 h-10 rounded-full bg-black/40 backdrop-blur-md hover:bg-black/60 transition"
          aria-label="Close camera"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Live Stability / Alignment Badge */}
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-black/40 backdrop-blur-md text-xs font-semibold">
          {isStable ? (
            <CheckCircle2 className="w-4 h-4 text-kiwi-lime" />
          ) : (
            <AlertCircle className="w-4 h-4 text-amber-400 animate-pulse" />
          )}
          <span>{stabilityFeedback}</span>
        </div>

        {/* Flash / Torch Toggle */}
        {hasTorch ? (
          <button
            type="button"
            onClick={toggleTorch}
            className={`flex items-center justify-center w-10 h-10 rounded-full backdrop-blur-md transition ${
              torchOn ? 'bg-amber-400 text-stone-950 shadow-md' : 'bg-black/40 hover:bg-black/60 text-white'
            }`}
            aria-label="Toggle flash"
          >
            {torchOn ? <Zap className="w-5 h-5 fill-current" /> : <ZapOff className="w-5 h-5" />}
          </button>
        ) : (
          <div className="w-10 h-10" />
        )}
      </div>

      {/* Video Viewport with Document Framing Guide */}
      <div className="relative w-full h-[460px] sm:h-[520px] rounded-2xl overflow-hidden flex items-center justify-center bg-stone-950">
        {cameraError ? (
          <div className="flex flex-col items-center gap-3 p-6 text-center text-stone-300">
            <AlertCircle className="w-10 h-10 text-rose-400" />
            <p className="text-sm font-medium">{cameraError}</p>
            <button
              type="button"
              onClick={() => startCamera(facingMode)}
              className="px-4 py-2 mt-2 text-xs font-bold text-white rounded-xl bg-kiwi-flesh hover:bg-kiwi-flesh/90 transition"
            >
              Retry Camera
            </button>
          </div>
        ) : (
          <>
            <video
              ref={videoRef}
              playsInline
              muted
              autoPlay
              className="w-full h-full object-cover"
            />
            {/* Minimalist framing reticle */}
            <div className="absolute inset-8 sm:inset-12 border-2 border-dashed border-white/50 rounded-2xl pointer-events-none transition-colors duration-300" />
          </>
        )}
      </div>

      {/* Bottom Shutter Controls */}
      <div className="flex items-center justify-around w-full max-w-sm mt-5 mb-2">
        {/* Flip Camera */}
        <button
          type="button"
          onClick={switchCamera}
          className="flex items-center justify-center w-12 h-12 rounded-full bg-white/10 text-white hover:bg-white/20 transition"
          aria-label="Switch camera"
        >
          <FlipHorizontal className="w-5 h-5" />
        </button>

        {/* Shutter Button */}
        <button
          type="button"
          onClick={takePicture}
          disabled={Boolean(cameraError) || isCapturing}
          className="relative flex items-center justify-center w-20 h-20 rounded-full border-4 border-white/80 p-1.5 transition active:scale-95 disabled:opacity-50"
          aria-label="Capture photo"
        >
          <div className="w-full h-full rounded-full bg-white flex items-center justify-center shadow-lg">
            <Camera className="w-7 h-7 text-stone-900" />
          </div>
        </button>

        <div className="w-12 h-12" />
      </div>
    </div>
  )
}

