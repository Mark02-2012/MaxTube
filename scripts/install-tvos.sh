#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 2 ]]; then
  echo "usage: $0 unsigned.ipa signed.ipa" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEAM_ID="${TVOS_TEAM_ID:-}"
DEVICE_ID="${TVOS_DEVICE_ID:-}"
BUNDLE_ID="${TVOS_BUNDLE_ID:-com.xsyetopz.maxtube.tvos}"

if [[ -z "${DEVELOPER_DIR:-}" ]] && [[ -d /Applications/Xcode-27.0.0.app/Contents/Developer ]]; then
  export DEVELOPER_DIR=/Applications/Xcode-27.0.0.app/Contents/Developer
fi

command -v codesign >/dev/null
command -v openssl >/dev/null
command -v plutil >/dev/null
command -v python3 >/dev/null
command -v security >/dev/null
command -v unzip >/dev/null
command -v xcodebuild >/dev/null
command -v xcrun >/dev/null
command -v zip >/dev/null

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

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
DERIVED_DATA="$WORK/DerivedData"
PROJECT="$ROOT/Tools/TVOSProvisioning/MaxTubeProvisioning.xcodeproj"

if [[ -z "$TEAM_ID" ]]; then
  CERTIFICATE_SUBJECT="$(security find-certificate -c 'Apple Development' -p | openssl x509 -noout -subject -nameopt RFC2253)"
  TEAM_ID="$(sed -n 's/.*OU=\([^,]*\).*/\1/p' <<<"$CERTIFICATE_SUBJECT")"
  if [[ -z "$TEAM_ID" ]]; then
    echo "could not detect an Apple Development team; set TVOS_TEAM_ID" >&2
    exit 1
  fi
fi

if [[ -z "$DEVICE_ID" ]]; then
  xcrun devicectl list devices --json-output "$WORK/devices.json" >/dev/null
  DEVICE_ID="$(python3 - "$WORK/devices.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    devices = json.load(handle)["result"]["devices"]

matches = [
    device["properties"]["hardware"]["udid"]
    for device in devices
    if device["properties"]["hardware"].get("platform") == "tvOS"
    and device["properties"]["hardware"].get("reality") == "physical"
]
if len(matches) != 1:
    raise SystemExit(
        f"expected one paired physical Apple TV, found {len(matches)}; set TVOS_DEVICE_ID"
    )
print(matches[0])
PY
)"
fi

xcodebuild \
  -project "$PROJECT" \
  -scheme MaxTubeProvisioning \
  -configuration Debug \
  -destination "platform=tvOS,id=$DEVICE_ID" \
  -derivedDataPath "$DERIVED_DATA" \
  -allowProvisioningUpdates \
  -allowProvisioningDeviceRegistration \
  -quiet \
  DEVELOPMENT_TEAM="$TEAM_ID" \
  PRODUCT_BUNDLE_IDENTIFIER="$BUNDLE_ID" \
  build

BOOTSTRAP_APP="$DERIVED_DATA/Build/Products/Debug-appletvos/MaxTubeProvisioning.app"
PROFILE="$BOOTSTRAP_APP/embedded.mobileprovision"
ENTITLEMENTS="$WORK/entitlements.plist"
CERTIFICATE_PREFIX="$WORK/signing-certificate"
codesign -d --extract-certificates="$CERTIFICATE_PREFIX" "$BOOTSTRAP_APP"
IDENTITY="$(openssl x509 -inform DER -in "${CERTIFICATE_PREFIX}0" -noout -fingerprint -sha1 | cut -d= -f2 | tr -d ':')"
if [[ -z "$IDENTITY" ]] || [[ ! -f "$PROFILE" ]]; then
  echo "Xcode did not produce a signed tvOS provisioning app" >&2
  exit 1
fi
codesign -d --xml --entitlements "$ENTITLEMENTS" "$BOOTSTRAP_APP"

unzip -q "$INPUT" -d "$WORK/package"
APP_COUNT="$(find "$WORK/package/Payload" -mindepth 1 -maxdepth 1 -type d -name '*.app' -print | wc -l | tr -d ' ')"
if [[ "$APP_COUNT" != "1" ]]; then
  echo "expected one Payload/*.app bundle, found $APP_COUNT" >&2
  exit 1
fi
APP="$(find "$WORK/package/Payload" -mindepth 1 -maxdepth 1 -type d -name '*.app' -print -quit)"

rm -rf "$APP/_CodeSignature" "$APP/SC_Info"
plutil -replace CFBundleIdentifier -string "$BUNDLE_ID" "$APP/Info.plist"
plutil -replace CFBundleDisplayName -string MaxTube "$APP/Info.plist"
if plutil -extract ITSDRMScheme raw "$APP/Info.plist" >/dev/null 2>&1; then
  plutil -remove ITSDRMScheme "$APP/Info.plist"
fi
cp "$PROFILE" "$APP/embedded.mobileprovision"

EXECUTABLE="$(plutil -extract CFBundleExecutable raw "$APP/Info.plist")"
chmod +x "$APP/$EXECUTABLE"
while IFS= read -r -d '' nested_binary; do
  chmod +x "$nested_binary"
  codesign --force --sign "$IDENTITY" --timestamp=none "$nested_binary"
done < <(find "$APP/Frameworks" -type f -name '*.dylib' -print0 2>/dev/null)

codesign \
  --force \
  --sign "$IDENTITY" \
  --entitlements "$ENTITLEMENTS" \
  --generate-entitlement-der \
  --timestamp=none \
  "$APP"
codesign --verify --deep --strict --verbose=2 "$APP"

SIGNED_TEMP="$WORK/signed.ipa"
(
  cd "$WORK/package"
  zip -qry "$SIGNED_TEMP" Payload
)
mv "$SIGNED_TEMP" "$OUTPUT"

xcrun devicectl device install app --device "$DEVICE_ID" "$APP"
xcrun devicectl device process launch \
  --device "$DEVICE_ID" \
  --terminate-existing \
  "$BUNDLE_ID"

echo "$OUTPUT"
