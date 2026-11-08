#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "usage: $0 tag title app.ipa release-notes.md" >&2
  exit 2
fi

command -v gh >/dev/null
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IPA="$3"
NOTES="$4"
[[ -f "$IPA" ]] || { echo "missing IPA: $IPA" >&2; exit 1; }
[[ -f "$NOTES" ]] || { echo "missing release notes: $NOTES" >&2; exit 1; }
if grep -q '%[a-z_]*%' "$NOTES"; then
  echo "release notes contain unresolved placeholders: $NOTES" >&2
  exit 1
fi

gh release create "$1" "$IPA" "$ROOT/THIRD_PARTY_NOTICES.md" \
  --draft \
  --title "$2" \
  --notes-file "$NOTES"
