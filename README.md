# Kiwi 🥝

**Kiwi** is a quiet, premium, local-first file conversion workspace. It runs completely offline on your own machine—transforming documents, images, audio, video, and archives with uncompromising privacy, bounded resource utilization, and an Apple-inspired utility aesthetic.

---

## Key Features & Highlights

- **Local-First & Offline Privacy:** All processing takes place in local temporary workspaces on your computer. Zero cloud storage, zero telemetry, no account requirements, and zero remote font/asset requests.
- **Quiet, Focused Design:** Minimal visual clutter, restrained neutrals with focused kiwi-green accents, a floating navigation capsule on desktop, a responsive bottom dock on mobile, and authentic local typography (`Unbounded` display face + `Host Grotesk` interface face).
- **Authoritative Conversion Registry:** Single-source strategy resolution (`server/app/core/formats.py`) with honest capability reporting (`ready`, `requires_engine`, `content_dependent`, `degraded_or_lossy`). No fake extension renaming.
- **Hardened Security & Resource Safety:**
  - Streaming upload quotas (512 MB per file, 1024 MB per request) with transactional cleanup on rejection (HTTP 413).
  - Bounded job queue (capacity 100) with admission control and HTTP 429 back-pressure.
  - Hard TTL retention (default 300s from job completion); downloading files does **not** push expiration forward.
  - Zip Slip path traversal mitigation, decompression bomb quotas (100:1 ratio, 10,000 files, 2 GB uncompressed max).
  - Process tree isolation with graceful cancellation via `psutil`.
  - Automatic log sanitization (redacting passwords and local filesystem paths).
- **Non-Destructive PDF & Media Processing:**
  - PDF compression uses Ghostscript vector/font subsetting or pikepdf/PyMuPDF lossless stream deflation—**never** destructive silent rasterization.
  - Office documents (DOCX, PPTX, XLSX) undergo container optimization with internal media asset recompression.
  - High-performance direct downloads via native browser anchors—avoiding multi-gigabyte Blob buffering in client RAM.

---

## Architecture Overview

```
[Browser Client]
  ├── React 18, TypeScript, Vite, Tailwind CSS
  ├── Local Fonts: Host Grotesk (UI) & Unbounded (Display)
  ├── Adaptive Bounded Polling with Tab Visibility Pausing & AbortController
  └── Native Anchor Streaming Downloads (No RAM Blob Exhaustion)
       │
       ▼ (multipart/form-data via fetch)
[FastAPI Backend]
  ├── core/uploads.py (Chunked streaming upload with strict byte quotas)
  ├── core/formats.py (Authoritative Strategy Registry & dynamic engine probe)
  └── routes/*.py (Pre-workspace validation & transactional cleanup)
       │
       ▼
[TaskQueue & JobStore]
  ├── Bounded Queue (maxsize=100) -> HTTP 429 when saturated
  ├── Worker Threads (global concurrency + per-engine locks)
  ├── Hard Expiration (TTL timed from completion timestamp)
  └── Automatic Workspace Purge (startup + periodic daemon sweep)
       │
       ▼
[Engine Services]
  ├── LibreOffice (soffice headless CLI)
  ├── Pandoc (AST document translation)
  ├── FFmpeg (audio/video transcoding, waveforms, frames)
  ├── Ghostscript & PyMuPDF (PDF tools, rendering, non-destructive compression)
  ├── Pillow & pillow-heif (Image re-encoding, AVIF, HEIF, ICO, TIFF)
  ├── Tesseract OCR (optical character recognition)
  └── py7zr, rarfile, zipfile, tarfile (safe archive processing)
```

---

## Supported Conversions & Capabilities

| Category | Formats | Primary Engine |
|---|---|---|
| **Documents** | PDF, DOCX, DOC, ODT, RTF, TXT, MD, HTML, EPUB, LaTeX, RST, Org, XML | LibreOffice, Pandoc, PyMuPDF |
| **Spreadsheets** | XLSX, XLS, ODS, CSV | openpyxl, LibreOffice, pdfplumber |
| **Presentations** | PPTX, PPT, ODP | LibreOffice, python-pptx |
| **Images** | JPG, PNG, WEBP, AVIF, GIF, BMP, TIFF, ICO, HEIC, SVG | Pillow, pillow-heif, CairoSVG |
| **Audio** | MP3, WAV, FLAC, OGG, OPUS, M4A, AAC, WMA | FFmpeg |
| **Video** | MP4, MKV, WEBM, AVI, MOV, M4V, MPEG, 3GP | FFmpeg |
| **Archives** | ZIP, 7Z, TAR, TAR.GZ, TAR.BZ2, TAR.XZ, RAR (Extract) | zipfile, py7zr, tarfile, rarfile |

For exhaustive conversion matrices, strategies, fidelity classifications, and semantic details (e.g. raster containment in SVG, table requirements for PDF-to-Excel), consult [`docs/SUPPORTED_FORMATS.md`](docs/SUPPORTED_FORMATS.md).

---

## Installation & Setup

### Prerequisites

- **Python:** 3.10 or newer
- **Node.js:** 18 or newer (with npm)

### 1. Server Setup

```powershell
cd server
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS / Linux

pip install -r requirements.txt
python run.py
```
*The FastAPI server starts at `http://127.0.0.1:8000`.*

### 2. Client Setup

```powershell
cd client
npm install
npm run dev
```
*The Vite frontend starts at `http://localhost:5173`.*

---

## Configuration (`.env`)

Copy `.env.example` to `.env` in the server root to customize settings:

```ini
# Upload Quotas
KIWI_MAX_UPLOAD_MB=512
KIWI_MAX_REQUEST_MB=1024
KIWI_MAX_FILE_COUNT=100

# Archive Safety
KIWI_MAX_ARCHIVE_ENTRIES=10000
KIWI_MAX_ARCHIVE_UNCOMPRESSED_MB=2048

# Queue & Retention
KIWI_MAX_QUEUE_SIZE=100
KIWI_WORKER_COUNT=2
KIWI_JOB_TTL_SECONDS=300
KIWI_CLEANUP_INTERVAL_SECONDS=15

# Strict Local CORS
KIWI_CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]

# Optional Binary Paths
KIWI_SOFFICE_BIN=soffice
KIWI_PANDOC_BIN=pandoc
KIWI_FFMPEG_BIN=ffmpeg
KIWI_GHOSTSCRIPT_BIN=gswin64c
KIWI_TESSERACT_BIN=tesseract
```

---

## Installing Local Engines (Optional)

Kiwi includes robust Python-native conversions out of the box. Installing external engines unlocks full office, media, OCR, and high-fidelity markup conversions:

### Windows (via winget)
```powershell
winget install TheDocumentFoundation.LibreOffice
winget install --id JohnMacFarlane.Pandoc
winget install Gyan.FFmpeg
winget install ArtifexSoftware.GhostScript
winget install UB-Mannheim.TesseractOCR
```

### macOS (via Homebrew)
```bash
brew install --cask libreoffice
brew install pandoc ffmpeg ghostscript tesseract
```

### Linux (Debian / Ubuntu)
```bash
sudo apt update
sudo apt install libreoffice pandoc ffmpeg ghostscript tesseract-ocr
```

---

## Running Verification & Tests

Kiwi includes automated backend test coverage and frontend unit tests:

### Backend Tests (pytest)
```powershell
cd server
.venv\Scripts\pytest server/tests -v
```
*Verifies upload streaming quotas (HTTP 413), admission control back-pressure (HTTP 429), Zip Slip security, decompression bomb rejection, log sanitization, job store hard TTL retention, image conversions (AVIF/HEIF/PNG), and non-destructive PDF compression.*

### Frontend Tests (vitest)
```powershell
cd client
npm test
```
*Verifies extension parsing, category classification, multi-file format intersections, and adaptive polling backoff.*

### Production Build Verification
```powershell
# Client TypeScript & Vite bundle
cd client
npm run build

# Python syntax compilation
cd server
python -m compileall app
```

---

## Documentation

- [`docs/IMPLEMENTATION_AUDIT.md`](docs/IMPLEMENTATION_AUDIT.md): Comprehensive architecture map, investigation and resolution of 28 repository defects, and security/lifecycle specifications.
- [`docs/SUPPORTED_FORMATS.md`](docs/SUPPORTED_FORMATS.md): Authoritative format conversion matrix, strategies, fidelity ratings, and engine requirements.

---

## License

MIT License. Designed and built with local-first privacy in mind.
