#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "usage: $0 input.ipa ytkace.deb output.ipa [extra.deb|extension.appex ...]" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if ! command -v cyan >/dev/null && [[ -x "$ROOT/dist/packaging-venv/bin/cyan" ]]; then
  export PATH="$ROOT/dist/packaging-venv/bin:$PATH"
fi
command -v cyan >/dev/null || { echo "Missing cyan; run just setup first." >&2; exit 1; }
command -v python3 >/dev/null
command -v unzip >/dev/null
command -v zip >/dev/null

absolute_existing_path() {
  local path="$1"
  if [[ ! -e "$path" ]]; then
    echo "missing input: $path" >&2
    return 1
  fi
  (cd "$(dirname "$path")" && printf '%s/%s\n' "$PWD" "$(basename "$path")")
}

INPUT="$(absolute_existing_path "$1")"
ENHANCER="$(absolute_existing_path "$2")"
OUTPUT="$3"
shift 3

mkdir -p "$(dirname "$OUTPUT")"
OUTPUT="$(cd "$(dirname "$OUTPUT")" && printf '%s/%s\n' "$PWD" "$(basename "$OUTPUT")")"

INJECTABLES=()
for injectable in "$@"; do
  INJECTABLES+=("$(absolute_existing_path "$injectable")")
done

DISPLAY_NAME="${APP_DISPLAY_NAME:-YouTube}"
BUNDLE_ID="${APP_BUNDLE_ID:-com.google.ios.youtube}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

unzip -q "$INPUT" -d "$WORK/input"
APP_COUNT="$(find "$WORK/input/Payload" -mindepth 1 -maxdepth 1 -type d -name '*.app' -print | wc -l | tr -d ' ')"
if [[ "$APP_COUNT" != "1" ]]; then
  echo "expected one Payload/*.app bundle, found $APP_COUNT" >&2
  exit 1
fi
APP="$(find "$WORK/input/Payload" -mindepth 1 -maxdepth 1 -type d -name '*.app' -print -quit)"

python3 - "$APP/Info.plist" <<'PY'
import plistlib
import sys

path = sys.argv[1]
with open(path, "rb") as handle:
    info = plistlib.load(handle)

platforms = info.get("CFBundleSupportedPlatforms", [])
if "iPhoneOS" not in platforms:
    raise SystemExit(f"unsupported base platform: {platforms!r}; expected iPhoneOS")

if info.get("CFBundleExecutable") != "YouTube":
    raise SystemExit("expected the YouTube app; YouTube Music is not supported by YTKACE")

families = set(info.get("UIDeviceFamily", []))
if not {1, 2}.issubset(families):
    raise SystemExit(
        f"the base must support both iPhone and iPad device families; found {sorted(families)!r}"
    )

minimum = info.get("MinimumOSVersion", "0")
parts = tuple(int(part) for part in minimum.split("."))
if parts < (15, 0):
    info["MinimumOSVersion"] = "15.0"
    with open(path, "wb") as handle:
        plistlib.dump(info, handle, fmt=plistlib.FMT_BINARY)

version = info.get("CFBundleShortVersionString", "unknown")
print(f"YouTube {version}; iOS/iPadOS minimum {info.get('MinimumOSVersion', minimum)}")
PY

PATCHED_IPA="$WORK/base-ios-ipados.ipa"
(
  cd "$WORK/input"
  zip -qry "$PATCHED_IPA" Payload
)

cyan \
  -i "$PATCHED_IPA" \
  -o "$OUTPUT" \
  -uwef "$ENHANCER" ${INJECTABLES[@]+"${INJECTABLES[@]}"} \
  -n "$DISPLAY_NAME" \
  -b "$BUNDLE_ID"

unzip -tq "$OUTPUT" >/dev/null
if ! python3 - "$OUTPUT" <<'PYZIP'
import sys
import zipfile

with zipfile.ZipFile(sys.argv[1]) as archive:
    present = any(name.endswith('/YTKACE.dylib') for name in archive.namelist())
raise SystemExit(0 if present else 1)
PYZIP
then
  echo "packaged IPA does not contain YTKACE.dylib" >&2
  exit 1
fi

echo "$OUTPUT"
