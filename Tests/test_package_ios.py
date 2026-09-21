import os
import plistlib
import stat
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SCRIPT = ROOT / "scripts" / "package-ios.sh"


class PackageIOSTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.work = Path(self.temporary_directory.name)
        self.bin = self.work / "bin"
        self.bin.mkdir()
        self.enhancer = self.work / "ytkace.deb"
        self.enhancer.write_bytes(b"test package")
        self._write_fake_cyan()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _write_fake_cyan(self):
        cyan = self.bin / "cyan"
        cyan.write_text(
            """#!/usr/bin/env python3
import shutil
import sys
import zipfile

arguments = sys.argv[1:]
source = arguments[arguments.index('-i') + 1]
output = arguments[arguments.index('-o') + 1]
shutil.copyfile(source, output)
with zipfile.ZipFile(output, 'a') as archive:
    archive.writestr('Payload/YouTube.app/Frameworks/YTKACE.dylib', b'test')
""",
            encoding="utf-8",
        )
        cyan.chmod(cyan.stat().st_mode | stat.S_IXUSR)

    def _make_ipa(self, *, platforms, families, minimum="14.0"):
        ipa = self.work / f"base-{len(list(self.work.glob('base-*.ipa')))}.ipa"
        info = {
            "CFBundleExecutable": "YouTube",
            "CFBundleIdentifier": "com.google.ios.youtube",
            "CFBundleShortVersionString": "21.33.6",
            "CFBundleSupportedPlatforms": platforms,
            "MinimumOSVersion": minimum,
            "UIDeviceFamily": families,
        }
        with zipfile.ZipFile(ipa, "w") as archive:
            archive.writestr(
                "Payload/YouTube.app/Info.plist",
                plistlib.dumps(info, fmt=plistlib.FMT_BINARY),
            )
            archive.writestr("Payload/YouTube.app/YouTube", b"executable")
        return ipa

    def _run(self, ipa):
        output = self.work / "output.ipa"
        environment = os.environ.copy()
        environment["PATH"] = f"{self.bin}:{environment['PATH']}"
        result = subprocess.run(
            [str(PACKAGE_SCRIPT), str(ipa), str(self.enhancer), str(output)],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        return result, output

    def test_packages_universal_base_and_enforces_ios_15_floor(self):
        ipa = self._make_ipa(platforms=["iPhoneOS"], families=[1, 2])

        result, output = self._run(ipa)

        self.assertEqual(result.returncode, 0, result.stderr)
        with zipfile.ZipFile(output) as archive:
            info = plistlib.loads(archive.read("Payload/YouTube.app/Info.plist"))
            self.assertEqual(info["MinimumOSVersion"], "15.0")
            self.assertIn(
                "Payload/YouTube.app/Frameworks/YTKACE.dylib",
                archive.namelist(),
            )

    def test_rejects_phone_only_base(self):
        ipa = self._make_ipa(platforms=["iPhoneOS"], families=[1])

        result, output = self._run(ipa)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("both iPhone and iPad", result.stderr)
        self.assertFalse(output.exists())

    def test_preserves_higher_base_minimum(self):
        ipa = self._make_ipa(platforms=["iPhoneOS"], families=[1, 2], minimum="17.0")

        result, output = self._run(ipa)

        self.assertEqual(result.returncode, 0, result.stderr)
        with zipfile.ZipFile(output) as archive:
            info = plistlib.loads(archive.read("Payload/YouTube.app/Info.plist"))
            self.assertEqual(info["MinimumOSVersion"], "17.0")

    def test_rejects_tvos_base(self):
        ipa = self._make_ipa(platforms=["AppleTVOS"], families=[3])

        result, output = self._run(ipa)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported base platform", result.stderr)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
