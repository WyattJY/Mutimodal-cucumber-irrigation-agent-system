#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
RECORDINGS_DIR="$DEMO_DIR/recordings"

INPUT_WEBM="${1:-}"
OUTPUT_MP4="${2:-$RECORDINGS_DIR/agriagent-ui-demo.mp4}"

if [[ -z "$INPUT_WEBM" ]]; then
  INPUT_WEBM="$(find "$RECORDINGS_DIR" -maxdepth 1 -type f -name '*.webm' | sort | tail -n 1 || true)"
fi

if [[ -z "$INPUT_WEBM" || ! -f "$INPUT_WEBM" ]]; then
  echo "No WebM recording found under $RECORDINGS_DIR"
  exit 1
fi

FFMPEG_BIN="${FFMPEG_BIN:-ffmpeg}"

if ! command -v "$FFMPEG_BIN" >/dev/null 2>&1; then
  cat <<'EOF'
Full ffmpeg is not installed on this computer.

macOS:
  brew install ffmpeg

Windows:
  winget install Gyan.FFmpeg

Then run:
  demo_cases/scripts/convert_recording_to_mp4.sh

If ffmpeg exists at a custom path, run:
  FFMPEG_BIN="/path/to/ffmpeg" demo_cases/scripts/convert_recording_to_mp4.sh
EOF
  exit 2
fi

"$FFMPEG_BIN" -y \
  -i "$INPUT_WEBM" \
  -c:v libx264 \
  -pix_fmt yuv420p \
  -movflags +faststart \
  "$OUTPUT_MP4"

echo "MP4 written to $OUTPUT_MP4"
