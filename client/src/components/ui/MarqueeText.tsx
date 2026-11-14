import { useState, useRef, useEffect, useCallback, type CSSProperties } from 'react'

interface MarqueeTextProps {
  text: string
  className?: string
  delayMs?: number
  speedPxPerSec?: number
}

/**
 * MarqueeText
 *
 * Automatically detects whether text overflows its bounding container.
 * If text overflows, hovering over the element for ~2-3 seconds initiates a
 * smooth, cyclic left-and-right animation at a constant readable speed.
 * Mouse exit immediately returns the text to its resting position.
 */
export function MarqueeText({
  text,
  className = '',
  delayMs = 2200,
  speedPxPerSec = 28,
}: MarqueeTextProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const textRef = useRef<HTMLSpanElement>(null)

  const [overflowDistance, setOverflowDistance] = useState<number>(0)
  const [isHovered, setIsHovered] = useState<boolean>(false)
  const [isAnimating, setIsAnimating] = useState<boolean>(false)

  // Measure text overflow against parent container
  const measure = useCallback(() => {
    if (!containerRef.current || !textRef.current) return
    const containerWidth = containerRef.current.clientWidth
    const textWidth = textRef.current.scrollWidth
    const diff = textWidth - containerWidth
    setOverflowDistance(diff > 2 ? diff : 0)
  }, [])

  useEffect(() => {
    measure()
    const observer = new ResizeObserver(() => measure())
    if (containerRef.current) observer.observe(containerRef.current)
    return () => observer.disconnect()
  }, [text, measure])

  // Delayed animation start on hover
  useEffect(() => {
    let timer: number | undefined
    if (isHovered && overflowDistance > 0) {
      timer = window.setTimeout(() => {
        setIsAnimating(true)
      }, delayMs)
    } else {
      setIsAnimating(false)
    }

    return () => {
      if (timer) window.clearTimeout(timer)
    }
  }, [isHovered, overflowDistance, delayMs])

  const handleMouseEnter = () => {
    setIsHovered(true)
  }

  const handleMouseLeave = () => {
    setIsHovered(false)
    setIsAnimating(false)
  }

  // Duration in seconds to travel out and back at constant speed
  const singleTripSeconds = Math.max(1.8, overflowDistance / speedPxPerSec)
  const cycleSeconds = singleTripSeconds * 2 + 1.2 // include pause at each end

  const animStyle: CSSProperties = isAnimating && overflowDistance > 0
    ? {
        transform: 'translateX(0)',
        animation: `marquee-pingpong ${cycleSeconds}s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite`,
        '--marquee-shift': `-${overflowDistance + 4}px`,
      } as any
    : {
        transform: 'translateX(0)',
        transition: 'transform 0.25s ease-out',
      }

  return (
    <div
      ref={containerRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      title={text}
      className={`relative overflow-hidden whitespace-nowrap min-w-0 ${className}`}
    >
      <span
        ref={textRef}
        style={animStyle}
        className="inline-block whitespace-nowrap"
      >
        {text}
      </span>
    </div>
  )
}
