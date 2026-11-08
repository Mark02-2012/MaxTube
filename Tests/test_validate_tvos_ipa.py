import plistlib
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate-tvos-ipa.py"
NORMALIZER = ROOT / "scripts" / "normalize-tvos-ipa.py"


class ValidateTVOSIPATest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.work = Path(self.temporary_directory.name)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _make_ipa(
        self,
        *,
        version="4.54.01",
        platforms=None,
        families=None,
        executable=b"executable",
    ):
        ipa = self.work / f"base-{len(list(self.work.glob('base-*.ipa')))}.ipa"
        info = {
            "CFBundleExecutable": "YouTubeUnstable",
            "CFBundleIdentifier": "com.google.ios.youtube",
            "CFBundleShortVersionString": version,
            "CFBundleSupportedPlatforms": platforms or ["AppleTVOS"],
            "MinimumOSVersion": "15.0",
            "UIDeviceFamily": families or [3],
        }
        with zipfile.ZipFile(ipa, "w") as archive:
            archive.writestr(
                "Payload/YouTube.app/Info.plist",
                plistlib.dumps(info, fmt=plistlib.FMT_BINARY),
            )
            archive.writestr("Payload/YouTube.app/YouTubeUnstable", executable)
        return ipa

    def _run(self, ipa, *arguments):
        return subprocess.run(
            [str(VALIDATOR), str(ipa), *arguments],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_accepts_matching_apple_tv_base(self):
        result = self._run(self._make_ipa(), "--expected-version", "4.54.01")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("YouTube 4.54.01; tvOS minimum 15.0", result.stdout)

    def test_rejects_ios_base(self):
        result = self._run(
            self._make_ipa(platforms=["iPhoneOS"], families=[1, 2]),
            "--expected-version",
            "4.54.01",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected AppleTVOS", result.stderr)

    def test_rejects_non_apple_tv_device_family(self):
        result = self._run(
            self._make_ipa(families=[1]),
            "--expected-version",
            "4.54.01",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Apple TV device family 3", result.stderr)

    def test_rejects_unpatched_youtube_version(self):
        result = self._run(
            self._make_ipa(version="4.55.00"),
            "--expected-version",
            "4.54.01",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires YouTube 4.54.01", result.stderr)

    def test_accepts_changed_executable_with_required_payload(self):
        original = self._make_ipa()
        patched = self._make_ipa(executable=b"patched https://example.test/script.js")

        result = self._run(
            patched,
            "--expected-version",
            "4.54.01",
            "--require-bytes",
            "https://example.test/script.js",
            "--different-executable-from",
            str(original),
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_unchanged_executable(self):
        original = self._make_ipa()
        result = self._run(
            original,
            "--expected-version",
            "4.54.01",
            "--different-executable-from",
            str(original),
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("patched executable is unchanged", result.stderr)


class NormalizeTVOSIPATest(unittest.TestCase):
    def test_removes_only_supported_device_restriction(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            source = work / "source.tipa"
            output = work / "output.ipa"
            info = {
                "CFBundleExecutable": "YouTubeUnstable",
                "CFBundleShortVersionString": "4.54.01",
                "CFBundleSupportedPlatforms": ["AppleTVOS"],
                "UIDeviceFamily": [3],
                "UISupportedDevices": ["AppleTV6,2", "AppleTV11,1"],
            }
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr(
                    "Payload/YouTube.app/Info.plist",
                    plistlib.dumps(info, fmt=plistlib.FMT_BINARY),
                )
                archive.writestr("Payload/YouTube.app/YouTubeUnstable", b"executable")
                archive.writestr("Payload/YouTube.app/resource", b"resource")

            result = subprocess.run(
                [str(NORMALIZER), str(source), str(output)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            with zipfile.ZipFile(output) as archive:
                normalized = plistlib.loads(
                    archive.read("Payload/YouTube.app/Info.plist")
                )
                self.assertNotIn("UISupportedDevices", normalized)
                self.assertEqual(
                    archive.read("Payload/YouTube.app/YouTubeUnstable"),
                    b"executable",
                )
                self.assertEqual(
                    archive.read("Payload/YouTube.app/resource"), b"resource"
                )

            with zipfile.ZipFile(source) as archive:
                original = plistlib.loads(
                    archive.read("Payload/YouTube.app/Info.plist")
                )
                self.assertEqual(
                    original["UISupportedDevices"],
                    ["AppleTV6,2", "AppleTV11,1"],
                )


if __name__ == "__main__":
    unittest.main()
