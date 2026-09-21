#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 2 ]]; then
  echo "usage: $0 input.ipa output.ipa" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../config/mutube.env
source "$ROOT/config/mutube.env"

command -v git >/dev/null
command -v python3 >/dev/null
command -v uv >/dev/null
command -v xcrun >/dev/null

absolute_existing_path() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "missing input: $path" >&2
    return 1
  fi
  (cd "$(dirname "$path")" && printf '%s/%s\n' "$PWD" "$(basename "$path")")
}

INPUT="$(absolute_existing_path "$1")"
OUTPUT="$2"
mkdir -p "$(dirname "$OUTPUT")"
OUTPUT="$(cd "$(dirname "$OUTPUT")" && printf '%s/%s\n' "$PWD" "$(basename "$OUTPUT")")"

python3 "$ROOT/scripts/validate-tvos-ipa.py" \
  "$INPUT" \
  --expected-version "$MUTUBE_YOUTUBE_VERSION"

if ! xcrun --sdk appletvos --show-sdk-path >/dev/null; then
  echo "the active Xcode developer directory has no AppleTVOS SDK" >&2
  echo "set DEVELOPER_DIR to Xcode.app/Contents/Developer and retry" >&2
  exit 1
fi

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
SOURCE="$WORK/mutube"
PATCHED="$WORK/patched.ipa"
NORMALIZED="$WORK/normalized.ipa"

git init --quiet "$SOURCE"
git -C "$SOURCE" remote add origin "$MUTUBE_REPOSITORY"
git -C "$SOURCE" fetch --quiet --depth 1 origin "$MUTUBE_REVISION"
ACTUAL_REVISION="$(git -C "$SOURCE" rev-parse FETCH_HEAD)"
if [[ "$ACTUAL_REVISION" != "$MUTUBE_REVISION" ]]; then
  echo "MuTube revision mismatch: expected $MUTUBE_REVISION, found $ACTUAL_REVISION" >&2
  exit 1
fi
git -C "$SOURCE" checkout --quiet --detach "$ACTUAL_REVISION"

cp "$ROOT/Resources/mutube-inject.js" "$SOURCE/inject.js"
sed -i.bak \
  -e "s/capstone>=5.0.6/capstone==$MUTUBE_CAPSTONE_VERSION/" \
  -e "s/lief>=0.17.3/lief==$MUTUBE_LIEF_VERSION/" \
  "$SOURCE/patcher.py"
PINNED_URL="https://cdn.jsdelivr.net/npm/@foxreis/tizentube@${TIZENTUBE_VERSION}/dist/userScript.js"
if ! grep -Fq "$PINNED_URL" "$SOURCE/inject.js"; then
  echo "MuTube payload does not match TizenTube $TIZENTUBE_VERSION" >&2
  exit 1
fi
if ! grep -Fq "capstone==$MUTUBE_CAPSTONE_VERSION" "$SOURCE/patcher.py" || \
  ! grep -Fq "lief==$MUTUBE_LIEF_VERSION" "$SOURCE/patcher.py"; then
  echo "failed to pin MuTube Python dependencies" >&2
  exit 1
fi

uv run --script "$SOURCE/patcher.py" \
  --in "$INPUT" \
  --out "$PATCHED"

python3 "$ROOT/scripts/normalize-tvos-ipa.py" "$PATCHED" "$NORMALIZED"

python3 "$ROOT/scripts/validate-tvos-ipa.py" \
  "$NORMALIZED" \
  --expected-version "$MUTUBE_YOUTUBE_VERSION" \
  --require-bytes "$PINNED_URL" \
  --different-executable-from "$INPUT"

mv "$NORMALIZED" "$OUTPUT"
echo "$OUTPUT"
