export type FileCategory = 'pdf' | 'image' | 'document' | 'spreadsheet' | 'presentation' | 'archive' | 'text' | 'audio' | 'video' | 'generic'

const EXT_CATEGORY: Record<string, FileCategory> = {
  pdf: 'pdf',
  jpg: 'image', jpeg: 'image', png: 'image', webp: 'image', avif: 'image', gif: 'image', bmp: 'image',
  tiff: 'image', tif: 'image', ico: 'image', heic: 'image', heif: 'image', svg: 'image',
  doc: 'document', docx: 'document', odt: 'document', rtf: 'document', epub: 'document',
  xls: 'spreadsheet', xlsx: 'spreadsheet', ods: 'spreadsheet', csv: 'spreadsheet',
  ppt: 'presentation', pptx: 'presentation', odp: 'presentation',
  zip: 'archive', '7z': 'archive', tar: 'archive', gz: 'archive', bz2: 'archive', xz: 'archive', rar: 'archive',
  md: 'text', markdown: 'text', txt: 'text', html: 'text', htm: 'text', tex: 'text', rst: 'text', org: 'text', xml: 'text',
  mp3: 'audio', wav: 'audio', flac: 'audio', ogg: 'audio', opus: 'audio', m4a: 'audio', aac: 'audio', wma: 'audio',
  mp4: 'video', mkv: 'video', webm: 'video', avi: 'video', mov: 'video', m4v: 'video', mpeg: 'video', mpg: 'video', '3gp': 'video',
}

export const CATEGORY_CLASSES: Record<FileCategory, string> = {
  pdf: 'bg-red-50 text-red-600 border-red-100 dark:bg-red-950/40 dark:text-red-400 dark:border-red-900/50',
  image: 'bg-sky-50 text-sky-600 border-sky-100 dark:bg-sky-950/40 dark:text-sky-400 dark:border-sky-900/50',
  document: 'bg-blue-50 text-blue-600 border-blue-100 dark:bg-blue-950/40 dark:text-blue-400 dark:border-blue-900/50',
  spreadsheet: 'bg-emerald-50 text-emerald-600 border-emerald-100 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-900/50',
  presentation: 'bg-orange-50 text-orange-600 border-orange-100 dark:bg-orange-950/40 dark:text-orange-400 dark:border-orange-900/50',
  archive: 'bg-violet-50 text-violet-600 border-violet-100 dark:bg-violet-950/40 dark:text-violet-400 dark:border-violet-900/50',
  text: 'bg-slate-50 text-slate-600 border-slate-100 dark:bg-slate-800/60 dark:text-slate-300 dark:border-slate-700/50',
  audio: 'bg-fuchsia-50 text-fuchsia-600 border-fuchsia-100 dark:bg-fuchsia-950/40 dark:text-fuchsia-400 dark:border-fuchsia-900/50',
  video: 'bg-rose-50 text-rose-600 border-rose-100 dark:bg-rose-950/40 dark:text-rose-400 dark:border-rose-900/50',
  generic: 'bg-stone-50 text-stone-600 border-stone-100 dark:bg-stone-800 dark:text-stone-300 dark:border-stone-700/50',
}

export function extensionOf(name: string): string {
  const lower = name.toLowerCase()
  for (const compound of ['tar.gz', 'tar.bz2', 'tar.xz']) {
    if (lower.endsWith(`.${compound}`)) return compound
  }
  return lower.includes('.') ? lower.split('.').pop()! : ''
}

export function categoryOf(nameOrExt: string): FileCategory {
  const ext = nameOrExt.includes('.') ? extensionOf(nameOrExt) : nameOrExt.toLowerCase()
  return EXT_CATEGORY[ext] ?? 'generic'
}

export function formatLabel(ext: string): string {
  const upper = ext.toUpperCase()
  return upper === 'JPEG' ? 'JPG' : upper
}
