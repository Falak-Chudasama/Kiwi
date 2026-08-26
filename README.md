# Kiwi

**Convert. Compress. Transform. Locally.**

Kiwi is a local-first file utility. It is designed to handle common document, PDF and image operations without uploading files to a cloud service.

## What works in this starter build

- Images → PDF, including multiple images into one PDF
- PDF merge
- PDF split / page extraction
- PDF → PNG/JPG/WebP
- PNG/JPG/WebP/TIFF/BMP → PNG/JPG/WebP/TIFF
- Image resize and compression
- Markdown → DOCX / PDF / HTML when Pandoc is installed
- TXT → PDF / DOCX
- DOCX → PDF when LibreOffice is installed
- PDF → TXT
- PDF metadata inspection
- Optional video/audio conversion through FFmpeg (engine included; UI exposes it when FFmpeg is detected)

Kiwi deliberately does **not** pretend every conversion is equally reliable. Format conversion is only offered where the local engine has a meaningful path.

## Architecture

```text
Kiwi UI (React/Vite)
        │
        │ localhost HTTP
        ▼
Kiwi API (FastAPI)
        │
        ├── Pillow
        ├── PyMuPDF
        ├── pypdf
        ├── python-docx
        ├── ReportLab
        ├── Pandoc (optional)
        ├── LibreOffice (optional)
        └── FFmpeg (optional)
```

No cloud API is used by the application.

## Requirements

- Python 3.11+
- Node.js 20+
- npm
- Windows/macOS/Linux

Optional engines:

- **Pandoc**: Markdown/document conversions
- **LibreOffice**: DOCX/ODT/XLSX/PPTX → PDF and related office conversions
- **FFmpeg**: audio/video conversion

The application still starts if optional engines are missing; their capabilities are simply unavailable.

## Install

### 1. Backend

Windows PowerShell:

```powershell
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

macOS/Linux:

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Frontend

Open a second terminal:

```bash
cd client
npm install
```

### 3. Optional local engines

Install these with your OS package manager or official installers:

- Pandoc: https://pandoc.org/installing.html
- LibreOffice: https://www.libreoffice.org/download/download-libreoffice/
- FFmpeg: https://ffmpeg.org/download.html

Kiwi checks for these executables locally. It does not download them at runtime.

## Run

Terminal 1:

```bash
cd server
# activate .venv first
python run.py
```

Terminal 2:

```bash
cd client
npm run dev
```

Open the Vite URL shown in the terminal, normally `http://localhost:5173`.

## Offline guarantee

At runtime Kiwi makes no outbound network requests. The frontend talks only to the local FastAPI server. Conversion engines execute as local processes/libraries.

For a strict offline environment, you can disconnect the machine after installing dependencies and optional engines.

## Build frontend

```bash
cd client
npm run build
```

The backend can serve the built frontend later; development mode keeps the two parts separate for easier iteration.

## Design principles

1. **File first** — drop a file and Kiwi figures out sensible operations.
2. **Minimal UI** — no converter catalogue or format maze.
3. **Local by default** — files stay on-device.
4. **Progressive complexity** — advanced options appear only when relevant.
5. **Honest capabilities** — unsupported or lossy conversions are not presented as magic.
