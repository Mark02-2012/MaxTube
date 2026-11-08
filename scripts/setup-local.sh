#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "$(uname -s)" != Darwin ]]; then
  echo "Local signing and installation require macOS and full Xcode." >&2
  exit 1
fi
command -v brew >/dev/null || { echo "Install Homebrew from https://brew.sh, then rerun just setup." >&2; exit 1; }
xcrun --sdk iphoneos --show-sdk-path >/dev/null || { echo "Install full Xcode and select it with xcode-select." >&2; exit 1; }
brew install dpkg ldid uv
uv venv --allow-existing "$ROOT/dist/packaging-venv"
uv pip install --python "$ROOT/dist/packaging-venv/bin/python" \
  https://github.com/asdfzxcvbn/pyzule-rw/archive/740d3716dcd98c20c000f12cdb88f1f0b2a533a4.zip
echo "Ready. Add your Apple account in Xcode → Settings → Accounts, enable Developer Mode, and pair the device."
