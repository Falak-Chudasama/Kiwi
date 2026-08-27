# Kiwi

Local-first file conversion, PDF tools, image tools, compression, and archives.

## Conversion coverage

The main converter accepts any file and builds its target list from the available local engines. It currently covers:

- Documents and markup: PDF, DOC/DOCX, ODT, RTF, TXT, Markdown, HTML, EPUB, LaTeX, RST, Org, XML, PPT/PPTX/ODP, and common spreadsheet formats.
- Images: JPG/JPEG, PNG, WebP, AVIF, GIF, BMP, TIFF, ICO, HEIC/HEIF, SVG.
- Audio/video: MP3, WAV, FLAC, OGG, Opus, M4A, AAC, WMA, MP4, MKV, WebM, AVI, MOV, M4V, MPEG/MPG, 3GP.
- Archives: ZIP, 7Z, TAR, plus TAR.GZ/TGZ, TAR.BZ2/TBZ2, TAR.XZ/TXZ and RAR extraction.
- Common code/data text files such as JSON, YAML, TOML, SQL, Python, JavaScript/TypeScript, CSS, Java, C/C++, C#, Go, Rust, PHP, Ruby, shell scripts, and logs can be treated as plain text for document export.

The converter does not fake incompatible transformations by changing an extension. Targets are disabled when the current engines cannot produce a meaningful result.

## Engines

Kiwi can use these local tools when installed:

1. LibreOffice — Office formats and PDF export.
2. Pandoc — document/markup conversion.
3. FFmpeg — audio/video transcoding and media rendering.
4. Tesseract OCR — image/PDF text extraction.
5. Pillow, pillow-heif, CairoSVG — image conversion.
6. pdfplumber, openpyxl, PyMuPDF — PDF tables, spreadsheets, PDF rendering/extraction.
7. py7zr and rarfile — 7Z/RAR archive support.

## Install

### Server

```powershell
cd server
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python run.py
```

### Client

```powershell
cd client
npm install
npm run dev
```

## Archive downloads

Extracted archives are returned as individual result files. **Download all** starts the individual file downloads; Kiwi does not create another ZIP just to download extracted contents.

## Temporary files

Each job uses a temporary OS workspace. Input files are removed after processing, and completed workspaces expire automatically.
