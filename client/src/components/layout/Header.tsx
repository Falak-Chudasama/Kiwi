import { NavLink, Link } from 'react-router-dom'
import kiwiMark from '../../assets/kiwi-mark.png'

const NAV = [
  { to: '/documents', label: 'Convert' },
  { to: '/images', label: 'Images' },
  { to: '/pdf', label: 'PDF' },
  { to: '/archives', label: 'Archives' },
  { to: '/engines', label: 'Engines' },
]

export function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-stone-200/80 bg-[#FAF8ED]/92 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center gap-5 px-4 py-3 sm:px-6">
        <Link to="/" className="focus-ring mr-auto flex items-center gap-2.5 rounded-xl">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white shadow-sm ring-1 ring-stone-200/80">
            <img src={kiwiMark} alt="Kiwi" className="h-7 w-7 object-contain" />
          </span>
          <span className="font-heading text-lg font-bold tracking-tight text-kiwi-ink">Kiwi</span>
        </Link>
        <nav className="hidden items-center gap-1 sm:flex" aria-label="Primary">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `rounded-xl px-3 py-2 text-sm font-semibold transition ${isActive ? 'bg-white text-kiwi-ink shadow-sm ring-1 ring-stone-200/80' : 'text-kiwi-ink/55 hover:bg-white/70 hover:text-kiwi-ink'}`}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <span className="rounded-full border border-kiwi-flesh-100 bg-white px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.14em] text-kiwi-flesh-700">Local</span>
      </div>
    </header>
  )
}
