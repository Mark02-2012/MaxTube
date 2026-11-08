import argparse
import datetime
import importlib.util
import plistlib
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "install_apple", ROOT / "scripts/install-apple.py"
)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def device(udid, platform="iOS", reality="physical"):
    return {
        "identifier": udid,
        "properties": {
            "hardware": {"udid": udid, "platform": platform, "reality": reality},
            "connection": {"pairingState": "paired"},
        },
    }


def profile():
    return {
        "ApplicationIdentifierPrefix": ["PREFIX"],
        "TeamIdentifier": ["TEAM"],
        "Entitlements": {"application-identifier": "PREFIX.com.example.youtube"},
        "ProvisionedDevices": ["phone"],
        "ExpirationDate": datetime.datetime.now() + datetime.timedelta(days=1),
    }


class InstallerSelectionTest(unittest.TestCase):
    def test_ignores_simulators_and_other_platforms(self):
        devices = [
            device("sim", reality="simulated"),
            device("tv", platform="tvOS"),
            device("phone"),
        ]
        self.assertEqual(installer.select_device(devices, "iOS"), "phone")

    def test_requires_explicit_device_when_ambiguous(self):
        devices = [device("one"), device("two")]
        with self.assertRaisesRegex(ValueError, "IOS_DEVICE_ID"):
            installer.select_device(devices, "iOS")
        self.assertEqual(installer.select_device(devices, "iOS", "two"), "two")

    def test_reuses_sideloaded_youtube_and_ignores_music(self):
        apps = [
            {"bundleIdentifier": "com.google.ios.youtube.TEAM"},
            {"bundleIdentifier": "com.google.ios.youtubemusic.TEAM"},
        ]
        self.assertEqual(
            installer.select_bundle(apps, "iOS", "com.google.ios.youtube"),
            "com.google.ios.youtube.TEAM",
        )

    def test_never_guesses_between_multiple_youtube_apps(self):
        apps = [
            {"bundleIdentifier": "com.google.ios.youtube.ONE"},
            {"bundleIdentifier": "com.google.ios.youtube.TWO"},
        ]
        with self.assertRaisesRegex(ValueError, "IOS_BUNDLE_ID"):
            installer.select_bundle(apps, "iOS", "com.google.ios.youtube")
        self.assertEqual(
            installer.select_bundle(apps, "iOS", "", "com.example.override"),
            "com.example.override",
        )

    def test_reuses_tvos_id_and_defaults_for_first_install(self):
        self.assertEqual(
            installer.select_bundle([], "tvOS", "com.google.youtube"),
            "com.xsyetopz.maxtube.tvos",
        )
        self.assertEqual(
            installer.select_bundle(
                [{"bundleIdentifier": "com.google.youtube"}],
                "tvOS",
                "com.google.youtube",
            ),
            "com.google.youtube",
        )

    def test_profile_must_match_app_team_device_and_expiration(self):
        installer.validate_profile(profile(), "com.example.youtube", "TEAM", "phone")
        for key, value in [
            ("TeamIdentifier", ["OTHER"]),
            ("ProvisionedDevices", ["other"]),
            ("ExpirationDate", datetime.datetime(2000, 1, 1)),
            ("Entitlements", {"application-identifier": "PREFIX.com.other"}),
        ]:
            invalid = profile()
            invalid[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                installer.validate_profile(
                    invalid, "com.example.youtube", "TEAM", "phone"
                )

    def test_archive_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ipa = root / "bad.ipa"
            with zipfile.ZipFile(ipa, "w") as archive:
                archive.writestr("../escape", "bad")
            with self.assertRaisesRegex(ValueError, "unsafe archive path"):
                installer.extract_ipa(ipa, root / "package")
            self.assertFalse((root / "escape").exists())


class InstallerFlowTest(unittest.TestCase):
    def test_install_only_follows_successful_signing_unless_sign_only(self):
        cases = [
            (platform, sign_only, failure)
            for platform in ("iOS", "tvOS")
            for sign_only, failure in ((True, False), (False, False), (False, True))
        ]
        for platform, sign_only, sign_failure in cases:
            with (
                self.subTest(
                    platform=platform, sign_only=sign_only, sign_failure=sign_failure
                ),
                tempfile.TemporaryDirectory() as directory,
            ):
                root = Path(directory)
                source = root / "input.ipa"
                with zipfile.ZipFile(source, "w") as archive:
                    archive.writestr(
                        "Payload/YouTube.app/Info.plist",
                        plistlib.dumps(
                            {
                                "CFBundleExecutable": "YouTube",
                                "CFBundleIdentifier": "com.google.ios.youtube",
                                "CFBundleSupportedPlatforms": [
                                    "iPhoneOS" if platform == "iOS" else "AppleTVOS"
                                ],
                            }
                        ),
                    )
                calls = []

                def fake_run(*args, _calls=calls, **kwargs):
                    _calls.append(tuple(str(a) for a in args))
                    if args[:3] == ("security", "cms", "-D"):
                        return subprocess.CompletedProcess(
                            args, 0, stdout=plistlib.dumps(profile())
                        )
                    if args[0] == "zip":
                        Path(args[2]).write_bytes(b"signed artifact")
                    return subprocess.CompletedProcess(args, 0)

                def fake_json(work, *args, _platform=platform):
                    if args == ("list", "devices"):
                        return {"devices": [device("phone", platform=_platform)]}
                    return {"apps": []}

                args = argparse.Namespace(
                    platform=platform,
                    input=source,
                    output=root / "signed.ipa",
                    sign_only=sign_only,
                )
                with (
                    patch.object(installer.shutil, "which", return_value="/tool"),
                    patch.object(installer, "run", side_effect=fake_run),
                    patch.object(installer, "device_json", side_effect=fake_json),
                    patch.object(
                        installer,
                        "sign_app",
                        side_effect=ValueError("signature invalid")
                        if sign_failure
                        else None,
                    ),
                    patch.dict(
                        installer.os.environ,
                        {
                            platform.upper() + "_TEAM_ID": "TEAM",
                            platform.upper() + "_DEVICE_ID": "",
                            platform.upper() + "_BUNDLE_ID": "com.example.youtube",
                        },
                    ),
                ):
                    if sign_failure:
                        with self.assertRaisesRegex(ValueError, "signature invalid"):
                            installer.install(args)
                        self.assertFalse(args.output.exists())
                    else:
                        installer.install(args)
                        self.assertTrue(args.output.exists())
                installed = any(
                    call[:4] == ("xcrun", "devicectl", "device", "install")
                    for call in calls
                )
                self.assertEqual(installed, not sign_only and not sign_failure)
