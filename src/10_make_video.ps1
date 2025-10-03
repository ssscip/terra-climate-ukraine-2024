Param(
  [int]$Fps = 6,
  [string]$FramesDir = "output/frames_local",
  [string]$OutFile = "output/video/final_video.mp4"
)

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
  Write-Error "ffmpeg not found in PATH. Install it first."; exit 1
}
if (-not (Test-Path $FramesDir)) {
  Write-Error "Frames directory $FramesDir missing. Run 09_generate_frames.py first."; exit 1
}

# Use sequential pattern; if glob order inconsistent, rely on natural name sort
$pattern = Join-Path $FramesDir 'frame_*.png'

ffmpeg -y -framerate $Fps -pattern_type glob -i $pattern -c:v libx264 -pix_fmt yuv420p -vf "scale=1080:-2" $OutFile

Write-Host "Video written to $OutFile"
