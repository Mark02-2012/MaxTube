#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../config/ytkace.env
source "$ROOT/config/ytkace.env"
if [[ $# -gt 1 ]]; then
  echo "usage: $0 [output.deb]" >&2
  exit 2
fi
OUTPUT="${1:-$ROOT/dist/ytkace.deb}"
mkdir -p "$(dirname "$OUTPUT")"
if [[ -f "$OUTPUT" ]] && [[ "$(shasum -a 256 "$OUTPUT" | cut -d ' ' -f1)" == "$YTKACE_RELEASE_SHA256" ]]; then
  echo "$OUTPUT"
  exit 0
fi
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
URL="$YTKACE_REPOSITORY"
URL="${URL%.git}/releases/download/v${YTKACE_VERSION}/com.itzzace.ytkace_${YTKACE_VERSION}_rootless.deb"
curl --fail --location --silent --show-error "$URL" --output "$WORK/ytkace.deb"
echo "$YTKACE_RELEASE_SHA256  $WORK/ytkace.deb" | shasum -a 256 --check
cp "$WORK/ytkace.deb" "$OUTPUT"
echo "$OUTPUT"
