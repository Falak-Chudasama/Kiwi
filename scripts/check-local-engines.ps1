Write-Host "Kiwi local engine check" -ForegroundColor Green
$tools = @("pandoc", "ffmpeg", "libreoffice", "soffice")
foreach ($tool in $tools) {
  $cmd = Get-Command $tool -ErrorAction SilentlyContinue
  if ($cmd) { Write-Host "[OK]   $tool -> $($cmd.Source)" }
  else { Write-Host "[MISS] $tool" }
}
Write-Host "Python and Node are checked separately by the run instructions."
