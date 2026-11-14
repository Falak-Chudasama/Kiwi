import { useState, useRef, useEffect, type ReactNode } from 'react'
import { ChevronDown, Check } from 'lucide-react'
import { playEnter } from '../../lib/sound'

export interface SelectOption {
  value: string | number
  label: string
  sublabel?: string
  icon?: ReactNode
}

interface CustomSelectProps {
  value: string | number
  onChange: (value: string) => void
  options: SelectOption[]
  label?: string
  placeholder?: string
  disabled?: boolean
  className?: string
  buttonClassName?: string
}

export function CustomSelect({
  value,
  onChange,
  options,
  label,
  placeholder = 'Select an option...',
  disabled = false,
  className = '',
  buttonClassName = '',
}: CustomSelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const selectedOption = options.find((opt) => String(opt.value) === String(value))

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false)
      }
    }
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown)
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen])

  const handleSelect = (val: string | number) => {
    onChange(String(val))
    setIsOpen(false)
    playEnter()
  }

  return (
    <div ref={containerRef} className={`relative text-left ${className}`}>
      {label && (
        <label className="block text-xs font-bold text-stone-500 dark:text-stone-400 mb-1.5 uppercase tracking-wider">
          {label}
        </label>
      )}

      {/* Trigger Button */}
      <button
        type="button"
        disabled={disabled}
        onClick={() => setIsOpen((prev) => !prev)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        className={`focus-ring flex w-full items-center justify-between gap-3 rounded-xl glass-card px-3.5 py-2.5 text-xs sm:text-sm font-semibold text-stone-900 dark:text-stone-100 shadow-2xs transition hover:bg-white/45 dark:hover:bg-white/[0.05] disabled:opacity-50 disabled:cursor-not-allowed ${buttonClassName}`}
      >
        <div className="flex items-center gap-2 truncate min-w-0">
          {selectedOption?.icon && <span className="shrink-0">{selectedOption.icon}</span>}
          <span className="truncate">{selectedOption ? selectedOption.label : placeholder}</span>
        </div>
        <ChevronDown
          className={`h-4 w-4 shrink-0 text-stone-400 dark:text-stone-500 transition-transform duration-200 ${
            isOpen ? 'rotate-180 text-stone-700 dark:text-stone-200' : ''
          }`}
        />
      </button>

      {/* Glassmorphic Dropdown Panel */}
      {isOpen && (
        <div
          role="listbox"
          tabIndex={-1}
          className="glass-panel absolute z-50 mt-1.5 w-full min-w-[180px] max-h-60 overflow-y-auto rounded-2xl p-1.5 shadow-lift animate-scale-in scrollbar-clean"
        >
          {options.map((opt) => {
            const isSelected = String(opt.value) === String(value)
            return (
              <button
                key={String(opt.value)}
                type="button"
                role="option"
                aria-selected={isSelected}
                onClick={() => handleSelect(opt.value)}
                className={`flex w-full items-center justify-between gap-2.5 rounded-xl px-3 py-2 text-xs sm:text-sm transition text-left ${
                  isSelected
                    ? 'bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 font-bold shadow-2xs'
                    : 'text-stone-700 dark:text-stone-200 hover:bg-stone-100/80 dark:hover:bg-white/[0.06]'
                }`}
              >
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  {opt.icon && <span className="shrink-0">{opt.icon}</span>}
                  <div className="truncate">
                    <p className="truncate font-medium">{opt.label}</p>
                    {opt.sublabel && (
                      <p
                        className={`text-[11px] truncate ${
                          isSelected ? 'opacity-80' : 'text-stone-400 dark:text-stone-500'
                        }`}
                      >
                        {opt.sublabel}
                      </p>
                    )}
                  </div>
                </div>
                {isSelected && <Check className="h-4 w-4 shrink-0" />}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
