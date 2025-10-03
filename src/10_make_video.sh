#!/usr/bin/env bash
set -euo pipefail

FRAMES_DIR="output/frames_local"
OUT_MP4="output/video/final_video.mp4"
FPS=6

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg not found. Install ffmpeg to proceed." >&2
  exit 1
fi

if [ ! -d "$FRAMES_DIR" ]; then
  echo "Frames directory $FRAMES_DIR missing. Run 09_generate_frames.py first." >&2
  exit 1
fi

# Pattern assumes frame_YYYY-MM-DD.png
ffmpeg -y -framerate $FPS -pattern_type glob -i "${FRAMES_DIR}/frame_*.png" \
  -c:v libx264 -pix_fmt yuv420p -vf "scale=1080:-2" "$OUT_MP4"

echo "Video written to $OUT_MP4"
