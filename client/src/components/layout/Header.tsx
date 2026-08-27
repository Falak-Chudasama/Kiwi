import { Link } from 'react-router-dom'
import kiwiMark from '../../assets/kiwi-mark.png'

export function Header() {
  return (
    <header className="border-b border-kiwi-shell-50/70 bg-white/70 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4 sm:px-6">
        <Link to="/" className="focus-ring flex items-center gap-2.5 rounded-xl">
          <img src={kiwiMark} alt="Kiwi" className="h-8 w-8 rounded-full" />
          <span className="font-heading text-lg font-bold text-kiwi-ink">Kiwi</span>
        </Link>
        <span className="text-xs font-medium uppercase tracking-[0.2em] text-kiwi-ink/35">
          Offline File Toolkit
        </span>
      </div>
    </header>
  )
}
