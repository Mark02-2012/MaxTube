set dotenv-load := false
set shell := ["bash", "-euo", "pipefail", "-c"]

root := justfile_directory()

default:
    @just --list

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
