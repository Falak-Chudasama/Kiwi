import { useCallback, useRef, useState } from 'react'

const API = 'http://127.0.0.1:8000'

type FileInfo = { id: string; name: string; size: number; mime: string; kind: string; capabilities: Capability[] }
type Capability = { id: string; label: string; description?: string; targets?: { id: string; label: string }[] }
type Job = { id: string; status: string; message?: string; download_url?: string; output_name?: string }

const fmt = (n:number) => n < 1024 ? `${n} B` : n < 1048576 ? `${(n/1024).toFixed(1)} KB` : `${(n/1048576).toFixed(1)} MB`

export default function App() {
  const [files, setFiles] = useState<FileInfo[]>([])
  const [active, setActive] = useState<FileInfo | null>(null)
  const [busy, setBusy] = useState(false)
  const [job, setJob] = useState<Job | null>(null)
  const [drag, setDrag] = useState(false)
  const input = useRef<HTMLInputElement>(null)

  const analyze = async (incoming: File[]) => {
    if (!incoming.length) return
    setBusy(true); setJob(null)
    try {
      const form = new FormData()
      incoming.forEach(f => form.append('files', f))
      const res = await fetch(`${API}/api/analyze`, { method: 'POST', body: form })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setFiles(data.files)
      setActive(data.files[0] ?? null)
    } catch (e) { setJob({ id:'', status:'error', message: e instanceof Error ? e.message : 'Could not analyze files.' }) }
    finally { setBusy(false) }
  }

  const onDrop = useCallback((e: React.DragEvent) => { e.preventDefault(); setDrag(false); analyze(Array.from(e.dataTransfer.files)) }, [])

  const process = async (operation: string, target?: string, options: Record<string,unknown> = {}) => {
    if (!files.length) return
    setBusy(true); setJob(null)
    try {
      const res = await fetch(`${API}/api/process`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ file_ids: files.map(f=>f.id), operation, target, options }) })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json(); setJob(data)
      if (data.download_url) window.location.href = `${API}${data.download_url}`
    } catch(e) { setJob({id:'', status:'error', message:e instanceof Error ? e.message : 'Processing failed.'}) }
    finally { setBusy(false) }
  }

  const operations = active?.capabilities ?? []
  const hasMultiple = files.length > 1

  return <main>
    <header><div className="brand"><span className="dot"/>kiwi</div><span className="privacy">local only</span></header>

    {!files.length ? <section className={`dropzone ${drag ? 'drag' : ''}`} onDragOver={e=>{e.preventDefault();setDrag(true)}} onDragLeave={()=>setDrag(false)} onDrop={onDrop} onClick={()=>input.current?.click()}>
      <input ref={input} hidden type="file" multiple onChange={e=>analyze(Array.from(e.target.files ?? []))}/>
      <div className="kiwi-mark">kiwi</div>
      <h1>Drop files here</h1><p>Convert, compress, merge and transform — on this device.</p>
      <button className="primary">Choose files</button>
      <small>No uploads. No cloud processing.</small>
    </section> : <section className="workspace">
      <div className="filesbar">
        <div><strong>{files.length} {files.length === 1 ? 'file' : 'files'}</strong><span>{files.reduce((a,f)=>a+f.size,0) ? ` · ${fmt(files.reduce((a,f)=>a+f.size,0))}` : ''}</span></div>
        <button className="ghost" onClick={()=>{setFiles([]);setActive(null);setJob(null)}}>Start over</button>
      </div>
      <div className="filelist">{files.map(f=><button key={f.id} className={`file ${active?.id===f.id?'selected':''}`} onClick={()=>setActive(f)}><span className="fileicon">{f.kind==='image'?'IMG':f.kind==='pdf'?'PDF':f.kind==='document'?'DOC':'FILE'}</span><span className="filename">{f.name}</span><span className="filesize">{fmt(f.size)}</span></button>)}</div>

      {hasMultiple && files.every(f=>f.kind==='pdf') && <ActionCard title="Merge PDFs" text="Combine these PDFs into one file." button="Merge into PDF" onClick={()=>process('merge_pdf')} />}
      {hasMultiple && files.every(f=>f.kind==='image') && <ActionCard title="Images to PDF" text="Turn these images into one PDF." button="Create PDF" onClick={()=>process('images_to_pdf')} />}

      {active && <div className="actions">
        <div className="section-title">{active.name}<span>{active.mime} · {fmt(active.size)}</span></div>
        {operations.map(op=><CapabilityCard key={op.id} cap={op} busy={busy} onClick={(target, options)=>process(op.id,target,options)}/>)}
      </div>}

      {job?.status === 'error' && <div className="error">{job.message}</div>}
      {job?.status === 'done' && <div className="success">Done. Your file should have downloaded.</div>}
      {busy && <div className="processing">Working locally…</div>}
    </section>}
    <footer>Kiwi runs locally. Optional conversion engines are detected on your machine.</footer>
  </main>
}

function ActionCard({title,text,button,onClick}:{title:string;text:string;button:string;onClick:()=>void}) { return <div className="card special"><div><h2>{title}</h2><p>{text}</p></div><button className="primary" onClick={onClick}>{button}</button></div> }
function CapabilityCard({cap,busy,onClick}:{cap:Capability;busy:boolean;onClick:(target?:string,options?:Record<string,unknown>)=>void}) {
  const [target,setTarget]=useState(cap.targets?.[0]?.id ?? '')
  const [quality,setQuality]=useState('balanced')
  return <div className="card"><div className="cardhead"><div><h2>{cap.label}</h2><p>{cap.description}</p></div></div>{cap.targets && <div className="choices">{cap.targets.map(t=><button key={t.id} className={target===t.id?'choice active':'choice'} onClick={()=>setTarget(t.id)}>{t.label}</button>)}</div>}{cap.id==='compress_image' && <div className="choices"><button className={quality==='small'?'choice active':'choice'} onClick={()=>setQuality('small')}>Smaller</button><button className={quality==='balanced'?'choice active':'choice'} onClick={()=>setQuality('balanced')}>Balanced</button><button className={quality==='quality'?'choice active':'choice'} onClick={()=>setQuality('quality')}>Quality</button></div>}<button disabled={busy} className="primary full" onClick={()=>onClick(target,{quality})}>{busy?'Working…':cap.id==='compress_image'?'Compress':cap.id==='extract_pdf_text'?'Extract text':'Convert'}</button></div>
}
