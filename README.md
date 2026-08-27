# Kiwi

A fully offline file toolkit — document conversion, image conversion, PDF tools,
compression, and archives. Everything runs on your machine. Nothing is uploaded
anywhere.

## What's inside

- `server/` — FastAPI backend. Handles all conversion, compression, and archive
  work using local engines (LibreOffice, Pandoc, Pillow, pikepdf, PyMuPDF,
  Ghostscript, Tesseract, py7zr). Jobs run in a background worker pool so large
  files don't block the app.
- `client/` — React + Tailwind frontend. Five feature pages, all local, no
  accounts, no limits.
- `nginx/` — Reverse proxy config and a systemd service file, so you can visit
  `http://kiwi.local` and have it just work.

---

## 1. System dependencies

Kiwi's backend shells out to a few well-known open-source tools. Install these
first (Ubuntu/Debian shown — adjust for your distro):

```bash
sudo apt update
sudo apt install -y \
  python3 python3-venv python3-pip \
  libreoffice \
  pandoc \
  ghostscript \
  tesseract-ocr \
  nginx \
  build-essential libjpeg-dev zlib1g-dev
```

- **LibreOffice** — office document ↔ PDF conversion, and the compression
  pipeline for docx/pptx/xlsx.
- **Pandoc** — markdown/html/epub/rtf conversions.
- **Ghostscript** (`gs`) — PDF compression. If it's missing, Kiwi automatically
  falls back to a slower rasterize-based compressor, so this is optional but
  recommended.
- **Tesseract** — OCR for the PDF Tools page.
- **nginx** — reverse proxy, so the app is reachable at a clean local address.

## 2. Backend setup

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Test it runs:

```bash
python run.py
```

You should see uvicorn start on `127.0.0.1:8420`. Stop it with `Ctrl+C` once
confirmed — nginx/systemd will manage it going forward.

## 3. Frontend build

```bash
cd client
npm install
npm run build
```

This produces a `dist/` folder — the static site nginx will serve.

## 4. Deploy files to their serving location

```bash
sudo mkdir -p /var/www/kiwi
sudo cp -r server /var/www/kiwi/
sudo cp -r client/dist /var/www/kiwi/client
```

(Copy the built `client/dist` contents to `/var/www/kiwi/client` — that's what
nginx's `root` in the config points at.)

Recreate the virtualenv in the deployed location if you copied it as-is, or
just copy `server/.venv` along with it — either works.

## 5. Point kiwi.local at your machine

Add this to `/etc/hosts`:

```
127.0.0.1   kiwi.local
```

## 6. Install the nginx site

```bash
sudo cp nginx/kiwi.conf /etc/nginx/sites-available/kiwi.conf
sudo ln -s /etc/nginx/sites-available/kiwi.conf /etc/nginx/sites-enabled/kiwi.conf
sudo nginx -t
sudo systemctl restart nginx
```

## 7. Run the backend as a background service

```bash
sudo cp nginx/kiwi-backend.service /etc/systemd/system/kiwi-backend.service
sudo systemctl daemon-reload
sudo systemctl enable --now kiwi-backend
```

Check it's alive:

```bash
sudo systemctl status kiwi-backend
curl http://127.0.0.1:8420/api/health
```

## 8. Open it

Visit **http://kiwi.local** in your browser. That's it.

---

## Notes

- All uploaded files and generated outputs live under `server/storage/` and are
  never sent anywhere else. Clean that folder periodically if disk space
  matters to you — nothing reads from old jobs after they're downloaded.
- `KIWI_WORKER_COUNT` (env var, default 2) controls how many conversion jobs
  run in parallel. Raise it if your machine has CPU to spare.
- To update the app later: pull new code, re-run `npm run build` in `client/`,
  re-copy `dist/` to `/var/www/kiwi/client`, and `sudo systemctl restart kiwi-backend`.
