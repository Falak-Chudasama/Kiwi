import { ArchiveIcon, CompressIcon, DocumentIcon, ImageStackIcon, PdfIcon } from '../components/ui/icons'
import { FeatureCard } from '../components/features/FeatureCard'

const FEATURES = [
  {
    to: '/documents',
    title: 'Document Conversion',
    description: 'Convert between docx, pdf, odt, markdown, html, and more.',
    icon: <DocumentIcon className="h-5 w-5" />,
  },
  {
    to: '/images',
    title: 'Image Conversion',
    description: 'Convert any image format, including HEIC, SVG, and ICO.',
    icon: <ImageStackIcon className="h-5 w-5" />,
  },
  {
    to: '/pdf',
    title: 'PDF Tools',
    description: 'Merge, split, rotate, watermark, protect, and OCR PDFs.',
    icon: <PdfIcon className="h-5 w-5" />,
  },
  {
    to: '/compress',
    title: 'Document Compression',
    description: 'Shrink PDFs, images, and office files by strength level.',
    icon: <CompressIcon className="h-5 w-5" />,
  },
  {
    to: '/archives',
    title: 'Archives',
    description: 'Create and extract zip, 7z, and tar archives.',
    icon: <ArchiveIcon className="h-5 w-5" />,
  },
]

export default function HomePage() {
  return (
    <main className="mx-auto w-full max-w-5xl px-4 py-14 sm:px-6">
      <div className="mx-auto max-w-xl text-center">
        <h1 className="font-heading text-3xl font-bold text-kiwi-ink sm:text-4xl">
          Your files. Your machine. Nothing leaves.
        </h1>
        <p className="mt-3 text-base text-kiwi-ink/55">
          Pick a tool below. Every conversion runs locally — no uploads, no limits, no accounts.
        </p>
      </div>

      <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((feature) => (
          <FeatureCard key={feature.to} {...feature} />
        ))}
      </div>
    </main>
  )
}
