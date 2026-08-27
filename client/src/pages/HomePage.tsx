import { Link } from 'react-router-dom'
import { ArrowRightLeft, ArchiveIcon, CompressIcon, ImageStackIcon, PdfIcon } from '../components/ui/icons'
import { FeatureCard } from '../components/features/FeatureCard'

const FEATURES = [
  { to: '/documents', title: 'Convert any file', description: 'One converter for documents, images, media, archives, and common data formats.', icon: <ArrowRightLeft className="h-6 w-6" />, tone: 'green' as const },
  { to: '/images', title: 'Image tools', description: 'Convert, resize, preview, and batch-process images.', icon: <ImageStackIcon className="h-6 w-6" />, tone: 'blue' as const },
  { to: '/pdf', title: 'PDF tools', description: 'Merge, split, rotate, protect, watermark, and OCR PDFs.', icon: <PdfIcon className="h-6 w-6" />, tone: 'red' as const },
  { to: '/compress', title: 'Compression', description: 'Shrink supported files and keep the smaller result.', icon: <CompressIcon className="h-6 w-6" />, tone: 'violet' as const },
  { to: '/archives', title: 'Archives', description: 'Create and extract ZIP, 7Z, TAR, and supported RAR files.', icon: <ArchiveIcon className="h-6 w-6" />, tone: 'orange' as const },
]

export default function HomePage() {
  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-12 sm:px-6 sm:py-16">
      <section className="mx-auto max-w-3xl text-center">
        <h1 className="font-heading text-4xl font-bold tracking-tight text-kiwi-ink sm:text-5xl">Convert, compress, and manage files.</h1>
        <p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-kiwi-ink/55">Pick a tool and work with the files already on your machine.</p>
        <Link to="/documents" className="focus-ring mt-6 inline-flex items-center gap-2 rounded-xl bg-kiwi-flesh px-4 py-2.5 text-sm font-bold text-white shadow-soft transition hover:bg-kiwi-flesh-600">
          Open converter <ArrowRightLeft className="h-4 w-4" />
        </Link>
      </section>

      <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((feature) => <FeatureCard key={feature.to} {...feature} />)}
      </div>
    </main>
  )
}
