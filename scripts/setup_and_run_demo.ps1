Param(
  [switch]$ForceReinstall,
  [switch]$WithVideo
)

$ErrorActionPreference = 'Stop'
Write-Host "[setup] Starting minimal demo setup..."

$venvPy = Join-Path $PSScriptRoot '..' | Resolve-Path | ForEach-Object { Join-Path $_ '.venv\Scripts\python.exe' }
$venvDir = Split-Path $venvPy -Parent
if (-not (Test-Path $venvPy)) {
  Write-Host "[setup] Creating virtual environment (.venv)" -ForegroundColor Cyan
  python -m venv .venv
}

$marker = Join-Path $venvDir '..\..' '.venv_installed_demo'
if ($ForceReinstall -or -not (Test-Path $marker)) {
  Write-Host "[setup] Installing demo requirements" -ForegroundColor Cyan
  & $venvPy -m pip install --upgrade pip wheel setuptools
  & $venvPy -m pip install -r requirements-demo.txt
  New-Item -ItemType File -Path $marker -Force | Out-Null
} else {
  Write-Host "[setup] Requirements already installed (use -ForceReinstall to reinstall)" -ForegroundColor Yellow
}

# Decide on video flag (skip if ffmpeg missing and user didn't force WithVideo)
$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
$runArgs = @('scripts/run_all_demo.py','--regenerate')
if (-not $ffmpeg -and -not $WithVideo) {
  $runArgs += '--no-video'
  Write-Host "[setup] ffmpeg not found -> running without video (add to PATH then re-run with -WithVideo)" -ForegroundColor Yellow
} elseif ($WithVideo -and -not $ffmpeg) {
  Write-Warning "-WithVideo requested but ffmpeg not found; skipping video."
  $runArgs += '--no-video'
}

Write-Host "[setup] Running demo: $($runArgs -join ' ')" -ForegroundColor Green
& $venvPy $runArgs

Write-Host "[setup] Done. Outputs: data_products/, docs/metrics.csv, output/frames_local/, output/video/ (if video)." -ForegroundColor Green