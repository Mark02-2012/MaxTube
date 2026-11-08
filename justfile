set dotenv-load := false
set shell := ["bash", "-euo", "pipefail", "-c"]

root := justfile_directory()

default:
    @just --list

# List paired devices and their UDIDs for IOS_DEVICE_ID / TVOS_DEVICE_ID.
devices:
    xcrun devicectl list devices

# Install local packaging tools (macOS/Homebrew; full Xcode required).
setup:
    {{ quote(root + "/scripts/setup-local.sh") }}

# Download the official pinned YTKACE DEB and verify its SHA-256.
fetch-enhancer output="dist/ytkace-release.deb":
    {{ quote(root + "/scripts/fetch-enhancer.sh") }} {{ quote(output) }}

# Package a decrypted YouTube IPA, then provision, sign, install, and launch.
deploy-ios input output="dist/MaxTube-iOS-signed.ipa":
    {{ quote(root + "/scripts/deploy-apple.sh") }} ios {{ quote(input) }} {{ quote(output) }}

# Package the supported tvOS base, then provision, sign, install, and launch.
deploy-tvos input output="dist/MaxTube-tvOS-signed.ipa":
    {{ quote(root + "/scripts/deploy-apple.sh") }} tvos {{ quote(input) }} {{ quote(output) }}

# Provision, sign, update, and launch an already packaged iPhone/iPad IPA.
install-ios input output="dist/MaxTube-iOS-signed.ipa":
    {{ quote(root + "/scripts/install-ios.sh") }} {{ quote(input) }} {{ quote(output) }}

# Sign an iPhone/iPad IPA without installing it.
sign-ios input output="dist/MaxTube-iOS-signed.ipa":
    {{ quote(root + "/scripts/install-ios.sh") }} {{ quote(input) }} {{ quote(output) }} --sign-only

# Sign a tvOS IPA without installing it.
sign-tvos input output="dist/MaxTube-tvOS-signed.ipa":
    {{ quote(root + "/scripts/install-tvos.sh") }} {{ quote(input) }} {{ quote(output) }} --sign-only

# Build the pinned YTKACE rootless package into dist/ytkace.deb.
build-enhancer output="dist/ytkace.deb":
    {{ quote(root + "/scripts/build-enhancer.sh") }} {{ quote(output) }}

# Package an iPhone/iPad YouTube IPA with YTKACE.
package input enhancer output="dist/MaxTube.ipa":
    {{ quote(root + "/scripts/package-ios.sh") }} {{ quote(input) }} {{ quote(enhancer) }} {{ quote(output) }}

# Package the supported Apple TV YouTube IPA with MuTube.
package-tvos input output="dist/MaxTube-tvOS.ipa":
    {{ quote(root + "/scripts/package-tvos.sh") }} {{ quote(input) }} {{ quote(output) }}

# Provision, sign, install, and launch an existing tvOS IPA on the configured Apple TV.
install-tvos input output="dist/MaxTube-tvOS-signed.ipa":
    {{ quote(root + "/scripts/install-tvos.sh") }} {{ quote(input) }} {{ quote(output) }}

# Publish an existing IPA as a draft GitHub release.
publish tag title ipa notes:
    {{ quote(root + "/scripts/publish-draft.sh") }} {{ quote(tag) }} {{ quote(title) }} {{ quote(ipa) }} {{ quote(notes) }}

# Run repository checks that do not require Apple SDKs.
check:
    bash -n scripts/*.sh
    actionlint
    python3 -m unittest discover -s Tests -v
