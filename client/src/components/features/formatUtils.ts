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
  pdf: 'bg-red-50 text-red-600 border-red-100',
  image: 'bg-sky-50 text-sky-600 border-sky-100',
  document: 'bg-blue-50 text-blue-600 border-blue-100',
  spreadsheet: 'bg-emerald-50 text-emerald-600 border-emerald-100',
  presentation: 'bg-orange-50 text-orange-600 border-orange-100',
  archive: 'bg-violet-50 text-violet-600 border-violet-100',
  text: 'bg-slate-50 text-slate-600 border-slate-100',
  audio: 'bg-fuchsia-50 text-fuchsia-600 border-fuchsia-100',
  video: 'bg-rose-50 text-rose-600 border-rose-100',
  generic: 'bg-stone-50 text-stone-600 border-stone-100',
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
