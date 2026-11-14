/**
 * Kiwi UI Sound Effects (SFX) Subsystem
 *
 * Provides tactile audio feedback for key interactions.
 * If the corresponding audio files do not exist in `/sfx/`, execution continues
 * completely silently with zero errors or console warnings.
 */

export type SoundCategory = 'scroll' | 'enter' | 'back' | 'failed' | 'notification'

const SFX_FILES: Record<SoundCategory, string> = {
  scroll: '/sfx/scroll.mp3',
  enter: '/sfx/enter.mp3',
  back: '/sfx/back.mp3',
  failed: '/sfx/failed.mp3',
  notification: '/sfx/notification.mp3',
}

// Master volume levels for calm, comfortable audio
const VOLUMES: Record<SoundCategory, number> = {
  scroll: 0.25,
  enter: 0.4,
  back: 0.35,
  failed: 0.45,
  notification: 0.45,
}

// Audio pool to allow quick overlap without lag
const audioCache: Partial<Record<SoundCategory, HTMLAudioElement>> = {}
let lastScrollTime = 0
const SCROLL_THROTTLE_MS = 140

/**
 * Play a UI sound effect if available.
 * Silently ignores missing files, playback blocks, or uninitialized audio environments.
 */
export function playSound(category: SoundCategory): void {
  if (typeof window === 'undefined' || typeof Audio === 'undefined') {
    return
  }

  // Throttle scroll sounds to avoid overwhelming repetitive audio
  if (category === 'scroll') {
    const now = Date.now()
    if (now - lastScrollTime < SCROLL_THROTTLE_MS) {
      return
    }
    lastScrollTime = now
  }

  try {
    let audio = audioCache[category]
    if (!audio) {
      audio = new Audio(SFX_FILES[category])
      audio.preload = 'auto'
      audio.volume = VOLUMES[category] ?? 0.4
      audioCache[category] = audio
    } else {
      audio.currentTime = 0
    }

    const promise = audio.play()
    if (promise && typeof promise.catch === 'function') {
      promise.catch(() => {
        // Autoplay policy or missing file: fail silently
      })
    }
  } catch {
    // Fail silently
  }
}

export const playEnter = () => playSound('enter')
export const playBack = () => playSound('back')
export const playFailed = () => playSound('failed')
export const playNotification = () => playSound('notification')
export const playScroll = () => playSound('scroll')
