#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 3 || ( "$1" != ios && "$1" != tvos ) ]]; then
  echo "usage: $0 ios|tvos decrypted-base.ipa signed-output.ipa" >&2
  exit 2
fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLATFORM="$1"
INPUT="$2"
OUTPUT="$3"
python3 - "$INPUT" "$OUTPUT" <<'PYINPUT'
from pathlib import Path
import sys
source, output = (Path(value).resolve() for value in sys.argv[1:])
if not source.is_file():
    raise SystemExit(f"missing input: {source}")
if source == output:
    raise SystemExit("signed output must differ from the decrypted base IPA")
PYINPUT
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
if [[ "$PLATFORM" == ios ]]; then
  "$ROOT/scripts/fetch-enhancer.sh" "$ROOT/dist/ytkace-release.deb"
  "$ROOT/scripts/package-ios.sh" "$INPUT" "$ROOT/dist/ytkace-release.deb" "$WORK/MaxTube.ipa"
else
  "$ROOT/scripts/package-tvos.sh" "$INPUT" "$WORK/MaxTube.ipa"
fi
"$ROOT/scripts/install-$PLATFORM.sh" "$WORK/MaxTube.ipa" "$OUTPUT"
