#!/usr/bin/env python3
import argparse
import plistlib
import sys
import zipfile
from pathlib import Path


def normalize(source: Path, output: Path):
    with zipfile.ZipFile(source) as input_archive:
        entries = input_archive.infolist()
        info_entries = [
            entry
            for entry in entries
            if entry.filename.startswith("Payload/")
            and entry.filename.count("/") == 2
            and entry.filename.endswith(".app/Info.plist")
        ]
        if len(info_entries) != 1:
            raise ValueError(
                f"expected one Payload/*.app/Info.plist, found {len(info_entries)}"
            )

        info_entry = info_entries[0]
        info = plistlib.loads(input_archive.read(info_entry))
        removed = info.pop("UISupportedDevices", None)
        normalized_info = plistlib.dumps(info, fmt=plistlib.FMT_BINARY)

        with zipfile.ZipFile(output, "w") as output_archive:
            for entry in entries:
                data = (
                    normalized_info
                    if entry.filename == info_entry.filename
                    else input_archive.read(entry)
                )
                output_archive.writestr(entry, data)

    with zipfile.ZipFile(output) as archive:
        written_info = plistlib.loads(archive.read(info_entry.filename))
        if "UISupportedDevices" in written_info:
            raise ValueError("failed to remove UISupportedDevices")

    if removed:
        print(f"removed UISupportedDevices restriction: {removed!r}")
    else:
        print("UISupportedDevices restriction was not present")


def main():
    parser = argparse.ArgumentParser(
        description="Remove model-specific restrictions from a tvOS IPA"
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()

    try:
        normalize(arguments.input, arguments.output)
    except (OSError, ValueError, zipfile.BadZipFile, plistlib.InvalidFileException) as error:
        print(error, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
