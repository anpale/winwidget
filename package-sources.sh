#!/bin/sh
# Creates browser-agent-src.zip next to this script (sources only).
set -e
cd "$(dirname "$0")"
rm -f browser-agent-src.zip
zip -r browser-agent-src.zip . -x '.venv/*' '__pycache__/*' 'build/*' 'dist/*' 'installer/*' \
  '*.spec' '*.zip' 'shots/*' 'profile/*' '.git/*' '.DS_Store'
echo "Created $(pwd)/browser-agent-src.zip"
