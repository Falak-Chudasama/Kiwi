import type { SVGProps } from 'react'

type IconProps = SVGProps<SVGSVGElement>

const base = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.8,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
  viewBox: '0 0 24 24',
}

export function DocumentIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
      <path d="M14 3v5h5" />
      <path d="M9 13h6M9 17h6" />
    </svg>
  )
}

export function ImageStackIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <rect x="3" y="7" width="14" height="14" rx="2" />
      <path d="M7 3h14v14" />
      <circle cx="8.5" cy="12.5" r="1.5" />
      <path d="M5.5 20.5 10 15l3 3 3-4 2.5 2.5" />
    </svg>
  )
}

export function PdfIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
      <path d="M14 3v5h5" />
      <path d="M8.5 17v-4h1.2a1.2 1.2 0 1 1 0 2.4H8.5" />
      <path d="M12.5 17v-4h1a1.5 1.5 0 0 1 0 4h-1Z" />
      <path d="M17 13h-1.5v4M15.5 15h1.2" />
    </svg>
  )
}

export function CompressIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M8 3v4a1 1 0 0 1-1 1H3" />
      <path d="M16 3v4a1 1 0 0 0 1 1h4" />
      <path d="M8 21v-4a1 1 0 0 0-1-1H3" />
      <path d="M16 21v-4a1 1 0 0 1 1-1h4" />
    </svg>
  )
}

export function ArchiveIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <rect x="3" y="4" width="18" height="5" rx="1" />
      <path d="M5 9v9a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V9" />
      <path d="M10 13h4" />
    </svg>
  )
}

export function UploadCloudIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M7 17.5A4.5 4.5 0 0 1 7.5 8.6 6 6 0 0 1 19 10a4 4 0 0 1-1 7.9" />
      <path d="M12 12v8" />
      <path d="m9 15 3-3 3 3" />
    </svg>
  )
}

export function DownloadIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3v12" />
      <path d="m7 10 5 5 5-5" />
      <path d="M5 21h14" />
    </svg>
  )
}

export function ArrowRightIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M5 12h14" />
      <path d="m13 6 6 6-6 6" />
    </svg>
  )
}

export function ArrowLeftIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M19 12H5" />
      <path d="m11 18-6-6 6-6" />
    </svg>
  )
}

export function CloseIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="m6 6 12 12M18 6 6 18" />
    </svg>
  )
}

export function CheckCircleIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="m8.5 12.5 2.5 2.5 4.5-5.5" />
    </svg>
  )
}

export function AlertCircleIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 8v5" />
      <circle cx="12" cy="16" r="0.6" fill="currentColor" stroke="none" />
    </svg>
  )
}

export function SpinnerIcon(props: IconProps) {
  return (
    <svg {...base} viewBox="0 0 24 24" {...props}>
      <path d="M12 3a9 9 0 1 0 9 9" />
    </svg>
  )
}

export function TrashIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M4 7h16" />
      <path d="M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
      <path d="M6 7l1 13a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-13" />
      <path d="M10 11v6M14 11v6" />
    </svg>
  )
}

export function FileGenericIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
      <path d="M14 3v5h5" />
    </svg>
  )
}

export function LockIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <rect x="5" y="11" width="14" height="9" rx="2" />
      <path d="M8 11V7a4 4 0 0 1 8 0v4" />
    </svg>
  )
}

export function UnlockIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <rect x="5" y="11" width="14" height="9" rx="2" />
      <path d="M8 11V7a4 4 0 0 1 7.5-2" />
    </svg>
  )
}

export function RotateIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M4 12a8 8 0 1 1 2.6 5.9" />
      <path d="M4 20v-5h5" />
    </svg>
  )
}

export function WatermarkIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M7 3h10l4 4v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
      <path d="M9 16.5 15 8" />
    </svg>
  )
}

export function ScanTextIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M4 8V5a1 1 0 0 1 1-1h3" />
      <path d="M20 8V5a1 1 0 0 0-1-1h-3" />
      <path d="M4 16v3a1 1 0 0 0 1 1h3" />
      <path d="M20 16v3a1 1 0 0 1-1 1h-3" />
      <path d="M8 10h8M8 13h5" />
    </svg>
  )
}

export function LayersIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="m12 3 8 4.5-8 4.5-8-4.5Z" />
      <path d="m4 12 8 4.5 8-4.5" />
      <path d="m4 16.5 8 4.5 8-4.5" />
    </svg>
  )
}

export function ScissorsIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="6" cy="6" r="2.5" />
      <circle cx="6" cy="18" r="2.5" />
      <path d="m8 7.5 12 9.5" />
      <path d="m8 16.5 12-9.5" />
    </svg>
  )
}
