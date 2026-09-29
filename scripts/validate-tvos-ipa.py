#!/usr/bin/env python3
import argparse
import plistlib
import sys
import zipfile
from pathlib import Path


def read_app(ipa: Path):
    with zipfile.ZipFile(ipa) as archive:
        info_names = [
            name
            for name in archive.namelist()
            if name.startswith("Payload/")
            and name.count("/") == 2
            and name.endswith(".app/Info.plist")
        ]
        if len(info_names) != 1:
            raise ValueError(
                f"expected one Payload/*.app/Info.plist, found {len(info_names)}"
            )

        info_name = info_names[0]
        info = plistlib.loads(archive.read(info_name))
        executable_name = info.get("CFBundleExecutable")
        if not executable_name:
            raise ValueError("app has no CFBundleExecutable")

        executable_path = f"{info_name.removesuffix('Info.plist')}{executable_name}"
        try:
            executable = archive.read(executable_path)
        except KeyError as error:
            raise ValueError(f"app executable is missing: {executable_path}") from error

    return info, executable


def validate(ipa: Path, expected_version: str, required_bytes: bytes | None):
    info, executable = read_app(ipa)

    platforms = info.get("CFBundleSupportedPlatforms", [])
    if "AppleTVOS" not in platforms:
        raise ValueError(
            f"unsupported base platform: {platforms!r}; expected AppleTVOS"
        )

    families = set(info.get("UIDeviceFamily", []))
    if 3 not in families:
        raise ValueError(
            f"base must support Apple TV device family 3; found {sorted(families)!r}"
        )

    version = info.get("CFBundleShortVersionString", "unknown")
    if version != expected_version:
        raise ValueError(f"MuTube requires YouTube {expected_version}; found {version}")

    if required_bytes is not None and required_bytes not in executable:
        raise ValueError("patched executable does not contain the pinned TizenTube URL")

    minimum = info.get("MinimumOSVersion", "unknown")
    print(f"YouTube {version}; tvOS minimum {minimum}")
    return executable


def main():
    parser = argparse.ArgumentParser(description="Validate a MuTube tvOS IPA")
    parser.add_argument("ipa", type=Path)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--require-bytes")
    parser.add_argument("--different-executable-from", type=Path)
    arguments = parser.parse_args()

    try:
        executable = validate(
            arguments.ipa,
            arguments.expected_version,
            arguments.require_bytes.encode("ascii")
            if arguments.require_bytes
            else None,
        )
        if arguments.different_executable_from:
            _, original = read_app(arguments.different_executable_from)
            if executable == original:
                raise ValueError("patched executable is unchanged")
    except (
        OSError,
        ValueError,
        zipfile.BadZipFile,
        plistlib.InvalidFileException,
    ) as error:
        print(error, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
