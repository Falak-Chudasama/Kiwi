import { useEffect, useState } from 'react'
import { PageShell } from '../components/layout/PageShell'
import { ServerIcon, CopyIcon, CircleCheckIcon, CircleDashedIcon, SpinnerIcon } from '../components/ui/icons'
import { fetchSystemStatus, type EngineStatus } from '../lib/api'
import { useToast } from '../components/ui/ToastProvider'

type OS = 'windows' | 'macos' | 'linux'

function detectOS(): OS {
  const platform = navigator.userAgent.toLowerCase()
  if (platform.includes('mac')) return 'macos'
  if (platform.includes('linux') && !platform.includes('android')) return 'linux'
  return 'windows'
}

const OS_LABEL: Record<OS, string> = { windows: 'Windows', macos: 'macOS', linux: 'Linux' }

function EngineRow({ engine, os }: { engine: EngineStatus; os: OS }) {
  const { push } = useToast()
  const command = engine.install[os]

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(command)
      push('success', 'Install command copied.')
    } catch {
      push('error', 'Could not copy automatically — select and copy the command manually.')
    }
  }

  return (
    <div className={`rounded-2xl border p-4 ${engine.installed ? 'border-stone-100 bg-white' : 'border-kiwi-flesh-100 bg-kiwi-flesh-50/40'}`}>
      <div className="flex items-start gap-3">
        {engine.installed ? (
          <CircleCheckIcon className="mt-0.5 h-5 w-5 shrink-0 text-emerald-500" />
        ) : (
          <CircleDashedIcon className="mt-0.5 h-5 w-5 shrink-0 text-kiwi-ink/30" />
        )}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-heading text-sm font-bold text-kiwi-ink">{engine.name}</span>
            <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${engine.installed ? 'bg-emerald-50 text-emerald-600' : 'bg-stone-100 text-stone-500'}`}>
              {engine.installed ? 'Installed' : 'Not detected'}
            </span>
          </div>
          <p className="mt-1 text-sm leading-6 text-kiwi-ink/55">{engine.unlocks}</p>
          {!engine.installed && (
            <div className="mt-2.5 flex items-center gap-2">
              <code className="flex-1 truncate rounded-lg bg-stone-900 px-3 py-2 text-xs text-stone-100">{command}</code>
              <button
                type="button"
                onClick={copy}
                title="Copy install command"
                className="focus-ring shrink-0 rounded-lg border border-stone-200 bg-white p-2 text-kiwi-ink/60 transition hover:bg-stone-50 hover:text-kiwi-ink"
              >
                <CopyIcon className="h-3.5 w-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function EnginesPage() {
  const [engines, setEngines] = useState<EngineStatus[] | null>(null)
  const [os, setOs] = useState<OS>(detectOS())
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchSystemStatus()
      .then((data) => setEngines(data.engines))
      .catch((err) => setError(err instanceof Error ? err.message : 'Could not load engine status.'))
  }, [])

  return (
    <PageShell
      title="Conversion engines"
      description="Kiwi uses these local tools when they're installed. Missing ones just mean fewer targets are available — nothing is required to use the app."
      icon={<ServerIcon className="h-6 w-6" />}
    >
      <div className="mb-5 flex flex-wrap items-center gap-2">
        <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-kiwi-ink/35">Install commands for</span>
        <div className="flex gap-1 rounded-xl border border-stone-200 bg-white p-1">
          {(Object.keys(OS_LABEL) as OS[]).map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setOs(option)}
              className={`rounded-lg px-3 py-1.5 text-xs font-bold transition ${os === option ? 'bg-kiwi-flesh text-white' : 'text-kiwi-ink/55 hover:bg-stone-50'}`}
            >
              {OS_LABEL[option]}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="rounded-xl border border-red-100 bg-red-50 p-4 text-sm text-red-600">{error}</p>}

      {!engines && !error && (
        <div className="flex items-center gap-2 text-sm text-kiwi-ink/50">
          <SpinnerIcon className="h-4 w-4 animate-spin" />
          Checking installed engines…
        </div>
      )}

      {engines && (
        <div className="space-y-3">
          {engines.map((engine) => (
            <EngineRow key={engine.key} engine={engine} os={os} />
          ))}
        </div>
      )}
    </PageShell>
  )
}
