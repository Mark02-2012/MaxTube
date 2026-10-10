#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=config/ytkace.env
source "$ROOT/config/ytkace.env"

if [[ $# -gt 1 ]]; then
  echo "usage: $0 [output.deb]" >&2
  exit 2
fi

: "${THEOS:?Set THEOS to an installed Theos directory}"
command -v git >/dev/null
command -v make >/dev/null
command -v dpkg-deb >/dev/null

OUTPUT="${1:-$ROOT/dist/ytkace.deb}"
mkdir -p "$(dirname "$OUTPUT")"
OUTPUT="$(cd "$(dirname "$OUTPUT")" && pwd)/$(basename "$OUTPUT")"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
SOURCE="$WORK/ytkace"

git init --quiet "$SOURCE"
git -C "$SOURCE" remote add origin "$YTKACE_REPOSITORY"
git -C "$SOURCE" fetch --quiet --depth=1 origin "$YTKACE_REVISION"
git -C "$SOURCE" checkout --quiet --detach FETCH_HEAD

ACTUAL_REVISION="$(git -C "$SOURCE" rev-parse HEAD)"
if [[ "$ACTUAL_REVISION" != "$YTKACE_REVISION" ]]; then
  echo "expected YTKACE $YTKACE_REVISION, fetched $ACTUAL_REVISION" >&2
  exit 1
fi

make -C "$SOURCE" clean package \
  DEBUG=0 \
  FINALPACKAGE=1 \
  THEOS_PACKAGE_SCHEME=rootless

PACKAGE="$(find "$SOURCE/packages" -maxdepth 1 -type f -name '*.deb' -print -quit)"
PACKAGE_COUNT="$(find "$SOURCE/packages" -maxdepth 1 -type f -name '*.deb' -print | wc -l | tr -d ' ')"
if [[ "$PACKAGE_COUNT" != "1" ]]; then
  echo "expected one YTKACE package, found $PACKAGE_COUNT" >&2
  exit 1
fi

PACKAGE_VERSION="$(dpkg-deb -f "$PACKAGE" Version)"
if [[ "$PACKAGE_VERSION" != "$YTKACE_VERSION" ]]; then
  echo "expected YTKACE version $YTKACE_VERSION, built $PACKAGE_VERSION" >&2
  exit 1
fi

cp "$PACKAGE" "$OUTPUT"
echo "$OUTPUT"
