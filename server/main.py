from __future__ import annotations

import os, shutil, subprocess, tempfile, uuid
from pathlib import Path
from typing import Any

import fitz
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from PIL import Image
from pypdf import PdfReader, PdfWriter, PdfMerger
from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent
WORK = ROOT / ".kiwi-work"
WORK.mkdir(exist_ok=True)

app = FastAPI(title="Kiwi Local File Utility", docs_url="/api/docs", redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])

files: dict[str, Path] = {}

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".avif", ".gif"}
PDF_EXTS = {".pdf"}
DOC_EXTS = {".md", ".markdown", ".txt", ".docx", ".doc", ".odt", ".rtf", ".html", ".htm"}
VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v", ".mpeg", ".mpg"}
AUDIO_EXTS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".opus", ".m4a"}


def tool(name: str) -> str | None:
    return shutil.which(name)


def kind(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in IMAGE_EXTS: return "image"
    if ext in PDF_EXTS: return "pdf"
    if ext in VIDEO_EXTS: return "video"
    if ext in AUDIO_EXTS: return "audio"
    if ext in DOC_EXTS: return "document"
    return "file"


def mime(path: Path) -> str:
    import mimetypes
    return mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def target_list(*pairs: tuple[str,str]) -> list[dict[str,str]]:
    return [{"id": a, "label": b} for a,b in pairs]


def capabilities(path: Path) -> list[dict[str,Any]]:
    k, ext = kind(path), path.suffix.lower()
    out: list[dict[str,Any]] = []
    if k == "image":
        out.append({"id":"convert_image","label":"Convert","description":"Choose another image format.","targets":target_list(("jpg","JPG"),("png","PNG"),("webp","WebP"),("tiff","TIFF"))})
        out.append({"id":"compress_image","label":"Compress","description":"Reduce size while keeping the image usable."})
        out.append({"id":"images_to_pdf","label":"Image to PDF","description":"Create a PDF from this image."})
    elif k == "pdf":
        out.append({"id":"pdf_to_image","label":"Convert to images","description":"Render pages as image files.","targets":target_list(("png","PNG"),("jpg","JPG"),("webp","WebP"))})
        out.append({"id":"extract_pdf_text","label":"Extract text","description":"Create a plain-text copy of the PDF."})
        out.append({"id":"split_pdf","label":"Split PDF","description":"Create one PDF per page."})
    elif k == "document":
        targets=[]
        if ext in {".md",".markdown"} and tool("pandoc"):
            targets += [("docx","DOCX"),("pdf","PDF"),("html","HTML")]
        if ext == ".txt": targets += [("pdf","PDF"),("docx","DOCX")]
        if ext in {".docx",".odt",".rtf"} and tool("libreoffice"):
            targets += [("pdf","PDF")]
        if targets: out.append({"id":"convert_document","label":"Convert","description":"Use the best local document engine available.","targets":target_list(*targets)})
    elif k in {"video","audio"} and tool("ffmpeg"):
        if k == "video": targets=target_list(("mp4","MP4"),("webm","WebM"),("gif","GIF"))
        else: targets=target_list(("mp3","MP3"),("wav","WAV"),("flac","FLAC"),("m4a","M4A"))
        out.append({"id":"convert_media","label":"Convert","description":"Transcode with local FFmpeg.","targets":targets})
    return out


@app.get("/api/health")
def health():
    return {"ok":True,"offline":True,"engines":{"pandoc":bool(tool("pandoc")),"libreoffice":bool(tool("libreoffice") or tool("soffice")),"ffmpeg":bool(tool("ffmpeg"))}}


@app.post("/api/analyze")
async def analyze(files_upload: list[UploadFile] = File(...)):
    result=[]
    for upload in files_upload:
        fid=uuid.uuid4().hex
        safe=Path(upload.filename or "file").name
        dest=WORK / f"{fid}_{safe}"
        with dest.open("wb") as f:
            while chunk:=await upload.read(1024*1024): f.write(chunk)
        files[fid]=dest
        result.append({"id":fid,"name":safe,"size":dest.stat().st_size,"mime":mime(dest),"kind":kind(dest),"capabilities":capabilities(dest)})
    return {"files":result}


class ProcessRequest(BaseModel):
    file_ids: list[str]
    operation: str
    target: str | None = None
    options: dict[str,Any] = {}


def require_ids(ids:list[str]) -> list[Path]:
    if not ids: raise HTTPException(400,"No files supplied")
    try: return [files[x] for x in ids]
    except KeyError: raise HTTPException(404,"File session expired; please select the files again.")


def pdf_images(paths:list[Path], target:str) -> Path:
    out=WORK/f"{uuid.uuid4().hex}_pages"; out.mkdir()
    doc=fitz.open(paths[0])
    for i,page in enumerate(doc):
        pix=page.get_pixmap(matrix=fitz.Matrix(1.6,1.6), alpha=False)
        ext="jpg" if target=="jpg" else target
        p=out/f"page-{i+1}.{ext}"
        pix.save(str(p))
    zip_path=WORK/f"{uuid.uuid4().hex}_pages.zip"
    shutil.make_archive(str(zip_path.with_suffix('')),"zip",out)
    shutil.rmtree(out,ignore_errors=True)
    return zip_path


def image_convert(paths:list[Path], target:str, quality:str="balanced") -> Path:
    outdir=WORK/f"{uuid.uuid4().hex}_images"; outdir.mkdir()
    q={"small":65,"balanced":82,"quality":94}.get(quality,82)
    ext=target.lower(); actual="jpg" if ext=="jpg" else ext
    for src in paths:
        im=Image.open(src)
        if actual in {"jpg","jpeg"}:
            if im.mode not in {"RGB","L"}: im=im.convert("RGB")
            saveopt={"quality":q,"optimize":True}
        else:
            saveopt={"quality":q,"optimize":True} if actual=="webp" else {}
        dest=outdir/f"{src.stem}.{actual}"
        im.save(dest,format="JPEG" if actual=="jpg" else actual.upper(),**saveopt)
    if len(paths)==1: return next(outdir.iterdir())
    archive=WORK/f"{uuid.uuid4().hex}_converted.zip"; shutil.make_archive(str(archive.with_suffix('')),"zip",outdir); shutil.rmtree(outdir,ignore_errors=True); return archive


def images_to_pdf(paths:list[Path]) -> Path:
    imgs=[]
    for p in paths:
        im=Image.open(p).convert("RGB")
        imgs.append(im)
    out=WORK/f"{uuid.uuid4().hex}.pdf"
    imgs[0].save(out,save_all=True,append_images=imgs[1:])
    return out


def text_to_pdf(src:Path) -> Path:
    out=WORK/f"{uuid.uuid4().hex}.pdf"
    c=canvas.Canvas(str(out),pagesize=A4); width,height=A4; y=height-48
    c.setFont("Helvetica",10)
    for raw in src.read_text(encoding="utf-8",errors="replace").splitlines():
        line=raw[:115]
        c.drawString(42,y,line); y-=14
        if y<42: c.showPage(); c.setFont("Helvetica",10); y=height-48
    c.save(); return out


def text_to_docx(src:Path) -> Path:
    out=WORK/f"{uuid.uuid4().hex}.docx"; doc=Document()
    for line in src.read_text(encoding="utf-8",errors="replace").splitlines(): doc.add_paragraph(line)
    doc.save(out); return out


def run_cmd(args:list[str], cwd:Path|None=None):
    try: subprocess.run(args,cwd=cwd,check=True,capture_output=True,text=True,timeout=300)
    except FileNotFoundError: raise HTTPException(400,f"Required local engine is not installed: {args[0]}")
    except subprocess.CalledProcessError as e: raise HTTPException(400,e.stderr[-1500:] or "Local conversion engine failed.")
    except subprocess.TimeoutExpired: raise HTTPException(408,"Conversion took too long and was stopped.")


@app.post("/api/process")
def process(req: ProcessRequest):
    paths=require_ids(req.file_ids)
    op=req.operation; target=(req.target or "").lower(); quality=str(req.options.get("quality","balanced"))
    try:
        if op=="merge_pdf":
            if not all(p.suffix.lower()==".pdf" for p in paths): raise HTTPException(400,"All selected files must be PDFs.")
            out=WORK/f"{uuid.uuid4().hex}_merged.pdf"; merger=PdfMerger()
            for p in paths: merger.append(str(p))
            merger.write(str(out)); merger.close()
        elif op=="images_to_pdf": out=images_to_pdf(paths)
        elif op=="convert_image": out=image_convert(paths,target,quality)
        elif op=="compress_image": out=image_convert(paths,paths[0].suffix.lower().lstrip('.') if paths[0].suffix.lower() in {'.jpg','.jpeg','.png','.webp','.tiff'} else 'webp',quality)
        elif op=="pdf_to_image": out=pdf_images(paths,target)
        elif op=="extract_pdf_text":
            text="\n\n".join(page.get_text() for page in fitz.open(paths[0]))
            out=WORK/f"{paths[0].stem}_extracted.txt"; out.write_text(text,encoding="utf-8")
        elif op=="split_pdf":
            doc=fitz.open(paths[0]); outdir=WORK/f"{uuid.uuid4().hex}_split"; outdir.mkdir()
            for i in range(len(doc)):
                one=fitz.open(); one.insert_pdf(doc,from_page=i,to_page=i); one.save(outdir/f"{paths[0].stem}_page_{i+1}.pdf"); one.close()
            archive=WORK/f"{uuid.uuid4().hex}_split.zip"; shutil.make_archive(str(archive.with_suffix('')),"zip",outdir); shutil.rmtree(outdir,ignore_errors=True); out=archive
        elif op=="convert_document":
            src=paths[0]
            if src.suffix.lower()==".txt" and target=="pdf": out=text_to_pdf(src)
            elif src.suffix.lower()==".txt" and target=="docx": out=text_to_docx(src)
            elif target in {"docx","pdf","html"} and tool("pandoc"):
                out=WORK/f"{uuid.uuid4().hex}.{target}"; run_cmd([tool("pandoc") or "pandoc",str(src),"-o",str(out)])
            elif target=="pdf":
                soffice=tool("libreoffice") or tool("soffice")
                if not soffice: raise HTTPException(400,"LibreOffice is not installed.")
                outdir=WORK/f"{uuid.uuid4().hex}"; outdir.mkdir(); run_cmd([soffice,"--headless","--convert-to","pdf","--outdir",str(outdir),str(src)]); out=next(outdir.glob("*.pdf"))
            else: raise HTTPException(400,"This conversion requires Pandoc or LibreOffice.")
        elif op=="convert_media":
            if not tool("ffmpeg"): raise HTTPException(400,"FFmpeg is not installed.")
            out=WORK/f"{uuid.uuid4().hex}.{target}"; run_cmd([tool("ffmpeg") or "ffmpeg","-y","-i",str(paths[0]),str(out)])
        else: raise HTTPException(400,"Unsupported operation.")
    except HTTPException: raise
    except Exception as e: raise HTTPException(500,str(e))
    return {"id":uuid.uuid4().hex,"status":"done","output_name":out.name,"download_url":f"/api/download/{out.name}"}


@app.get("/api/download/{name}")
def download(name:str):
    p=WORK/Path(name).name
    if not p.exists(): raise HTTPException(404,"Output expired.")
    return FileResponse(p,filename=p.name,media_type=mime(p))
