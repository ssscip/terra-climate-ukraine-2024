Param(
    [switch]$Regenerate,
    [switch]$SkipVideo
)

Write-Host "[run_all_demo] Checking conda environment..."
if (-not (Test-Path env:CONDA_PREFIX)) {
    Write-Warning "Conda environment not active. Activate with: conda activate terra-climate"
}

if ($Regenerate) {
    Write-Host "[run_all_demo] Regenerating synthetic data..."
    python scripts/demo_generate_mock_data.py --run-metrics --make-frames
} else {
    if (-not (Test-Path data_products/lst_event.nc)) {
        Write-Host "[run_all_demo] No existing synthetic data; generating..."
        python scripts/demo_generate_mock_data.py --run-metrics --make-frames
    } else {
        Write-Host "[run_all_demo] Synthetic data already present; updating metrics + frames"
        python src/08_metrics.py
        python src/09_generate_frames.py
    }
}

Write-Host "[run_all_demo] Building distribution histogram..."
python src/07_histogram_distribution.py

if (-not $SkipVideo) {
    Write-Host "[run_all_demo] Creating video (PowerShell variant)..."
    python src/10_make_video.ps1
}

Write-Host "[run_all_demo] Done. See output/video and output/frames_local."
