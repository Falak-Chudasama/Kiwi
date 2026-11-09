import { useNavigate, Link } from 'react-router-dom'
import {
  Archive,
  ArrowRight,
  ArrowRightLeft,
  FileText,
  Image as ImageIcon,
  Minimize2,
} from 'lucide-react'
import { Dropzone } from '../components/features/Dropzone'
import kiwiIcon from '../assets/kiwi-icon.svg'

const SHORTCUTS = [
  {
    to: '/convert',
    title: 'Universal Converter',
    description: 'Convert between documents, markup, spreadsheets, and media.',
    icon: ArrowRightLeft,
  },
  {
    to: '/images',
    title: 'Image Tools',
    description: 'Batch convert, resize, preview, and encode modern formats.',
    icon: ImageIcon,
  },
  {
    to: '/pdf',
    title: 'PDF Workspace',
    description: 'Merge, split, rotate, reorder, protect, watermark, and OCR.',
    icon: FileText,
  },
  {
    to: '/compress',
    title: 'Compression',
    description: 'Optimize PDFs, images, and documents with non-destructive preservation.',
    icon: Minimize2,
  },
  {
    to: '/archives',
    title: 'Archives',
    description: 'Create and safely extract ZIP, 7Z, TAR, and RAR archives.',
    icon: Archive,
  },
]

export default function HomePage() {
  const navigate = useNavigate()

  const handleFiles = (files: File[]) => {
    if (!files.length) return
    navigate('/convert', { state: { incomingFiles: files } })
  }

  return (
    <main className="mx-auto w-full max-w-4xl px-4 py-8 pb-24 sm:py-14 sm:pb-20">
      {/* Hero Header */}
      <section className="text-center mb-10">
        <div className="inline-flex items-center justify-center mb-5">
          <div className="flex h-16 w-16 items-center justify-center rounded-3xl bg-white dark:bg-[#181915] p-2.5 shadow-soft border border-black/[0.05] dark:border-white/[0.08]">
            <img src={kiwiIcon} alt="Kiwi" className="h-11 w-11 object-contain" />
          </div>
        </div>
        <h1 className="font-display text-4xl font-extrabold tracking-tight text-stone-900 dark:text-stone-50 sm:text-5xl lg:text-6xl">
          Quiet file conversion workspace.
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-base sm:text-lg text-stone-600 dark:text-stone-400 font-sans leading-relaxed">
          High-fidelity format conversion, non-destructive optimization, and archive tools.
        </p>
      </section>

      {/* Primary Drop Surface */}
      <section className="mb-14">
        <Dropzone
          onFiles={handleFiles}
          multiple
          hint="Drop any document, image, media, or archive to begin"
        />
      </section>

      {/* Specialized Tool Shortcuts */}
      <section>
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-stone-500 dark:text-stone-400 font-sans">
            Specialized Toolkits
          </h2>
          <span className="text-sm text-stone-400 dark:text-stone-500">Choose a dedicated mode</span>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {SHORTCUTS.map(({ to, title, description, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className="group flex flex-col justify-between rounded-2xl border border-black/[0.06] dark:border-white/[0.08] bg-white dark:bg-[#181915] p-6 shadow-soft transition hover:border-kiwi-flesh/50 dark:hover:border-kiwi-lime/50 hover:shadow-lift"
            >
              <div>
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-stone-100 dark:bg-stone-800 text-stone-700 dark:text-stone-300 transition group-hover:bg-kiwi-flesh/10 dark:group-hover:bg-kiwi-lime/10 group-hover:text-kiwi-flesh-700 dark:group-hover:text-kiwi-lime">
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="mt-4 text-base sm:text-lg font-bold text-stone-900 dark:text-stone-100 font-sans group-hover:text-kiwi-flesh-700 dark:group-hover:text-kiwi-lime transition">
                  {title}
                </h3>
                <p className="mt-2 text-sm text-stone-600 dark:text-stone-400 leading-relaxed font-sans">
                  {description}
                </p>
              </div>

              <div className="mt-5 flex items-center gap-1.5 text-sm font-semibold text-stone-400 dark:text-stone-500 group-hover:text-kiwi-flesh-700 dark:group-hover:text-kiwi-lime transition">
                <span>Open tool</span>
                <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
              </div>
            </Link>
          ))}
        </div>
      </section>
    </main>
  )
}
