#!/usr/bin/env bash
set -u
echo "Kiwi local engine check"
for tool in pandoc ffmpeg libreoffice soffice; do
  if command -v "$tool" >/dev/null 2>&1; then echo "[OK]   $tool -> $(command -v "$tool")"; else echo "[MISS] $tool"; fi
done
