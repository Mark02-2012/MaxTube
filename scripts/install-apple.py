#!/usr/bin/env python3
"""Provision, sign, and optionally install a packaged MaxTube IPA."""

import argparse
import datetime
import hashlib
import json
import os
import plistlib
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, **kwargs)


def device_json(work, *args):
    output = work / "device.json"
    run("xcrun", "devicectl", *args, "--json-output", output, stdout=subprocess.DEVNULL)
    return json.loads(output.read_text())["result"]


def select_device(devices, platform, requested=""):
    matches = []
    for device in devices:
        props = device.get("properties", {})
        hardware = props.get("hardware", device.get("hardwareProperties", {}))
        connection = props.get("connection", device.get("connectionProperties", {}))
        if (
            hardware.get("platform") != platform
            or hardware.get("reality") != "physical"
        ):
            continue
        udid = hardware.get("udid", "")
        if requested:
            if requested not in (udid, device.get("identifier")):
                continue
        elif connection.get("pairingState") != "paired":
            continue
        matches.append(udid)
    if len(matches) != 1:
        raise ValueError(
            f"expected one paired physical {platform} device, found {len(matches)}; "
            f"set {platform.upper()}_DEVICE_ID to its UDID"
        )
    return matches[0]


def select_bundle(apps, platform, packaged_id, override=""):
    if override:
        return override
    candidates = set()
    for app in apps:
        bundle = app["bundleIdentifier"]
        if (
            bundle == packaged_id
            or bundle == "com.google.ios.youtube"
            or bundle.startswith("com.google.ios.youtube.")
            or bundle == f"com.xsyetopz.maxtube.{platform.lower()}"
        ):
            candidates.add(bundle)
    if len(candidates) > 1:
        raise ValueError(
            f"multiple YouTube apps found: {', '.join(sorted(candidates))}; "
            f"set {platform.upper()}_BUNDLE_ID to the app to update"
        )
    return next(iter(candidates), f"com.xsyetopz.maxtube.{platform.lower()}")


def signing_team():
    # Identities can be duplicated after certificate renewal; deduplicate by team.
    identities = run(
        "security",
        "find-identity",
        "-v",
        "-p",
        "codesigning",
        capture_output=True,
        text=True,
    ).stdout
    teams = set()
    certificates = run(
        "security",
        "find-certificate",
        "-a",
        "-c",
        "Apple Development",
        "-p",
        capture_output=True,
        text=True,
    ).stdout
    for pem in re.findall(
        r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----",
        certificates,
        re.DOTALL,
    ):
        der = run(
            "openssl",
            "x509",
            "-outform",
            "DER",
            input=pem.encode(),
            capture_output=True,
        ).stdout
        if hashlib.sha1(der).hexdigest().upper() not in identities:
            continue
        subject = run(
            "openssl",
            "x509",
            "-noout",
            "-subject",
            "-nameopt",
            "RFC2253",
            input=pem,
            capture_output=True,
            text=True,
        ).stdout
        match = re.search(
            r"(?:^|,)OU=([A-Z0-9]+)(?:,|$)", subject.replace("subject=", "")
        )
        if match:
            teams.add(match[1])
    if len(teams) != 1:
        raise ValueError(
            "could not select a single Apple Development team; "
            "set IOS_TEAM_ID or TVOS_TEAM_ID, and add your account in Xcode → Settings → Accounts"
        )
    return teams.pop()


def validate_profile(profile, bundle, team, device):
    identifier = profile["Entitlements"]["application-identifier"]
    prefix = profile["ApplicationIdentifierPrefix"][0]
    if identifier != f"{prefix}.{bundle}" and identifier != f"{prefix}.*":
        raise ValueError(f"profile does not authorize {bundle}")
    if team not in profile.get("TeamIdentifier", []):
        raise ValueError("profile belongs to a different signing team")
    if device not in profile.get("ProvisionedDevices", []):
        raise ValueError("profile does not include the selected device")
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    if profile["ExpirationDate"] <= now:
        raise ValueError("signing profile has expired")


def extract_ipa(source, destination):
    with zipfile.ZipFile(source) as archive:
        for member in archive.infolist():
            target = destination / member.filename
            if not target.resolve().is_relative_to(destination.resolve()):
                raise ValueError("IPA contains an unsafe archive path")
            mode = member.external_attr >> 16
            if mode & 0o170000 == 0o120000:
                raise ValueError("IPA contains unsupported symbolic links")
        archive.extractall(destination)
        for member in archive.infolist():
            mode = member.external_attr >> 16
            if mode:
                (destination / member.filename).chmod(mode & 0o777)
    apps = list((destination / "Payload").glob("*.app"))
    if len(apps) != 1:
        raise ValueError(f"expected one Payload/*.app, found {len(apps)}")
    return apps[0]


def sign_app(app, bootstrap, work):
    profile_path = bootstrap / "embedded.mobileprovision"
    entitlements = work / "entitlements.plist"
    certificate = str(work / "certificate")
    run("codesign", "-d", "--xml", "--entitlements", entitlements, bootstrap)
    run("codesign", "-d", "--extract-certificates=" + certificate, bootstrap)
    identity = hashlib.sha1(Path(certificate + "0").read_bytes()).hexdigest().upper()
    shutil.copy2(profile_path, app / "embedded.mobileprovision")
    for name in ("_CodeSignature", "SC_Info"):
        shutil.rmtree(app / name, ignore_errors=True)
    info = plistlib.loads((app / "Info.plist").read_bytes())
    main = app / info["CFBundleExecutable"]
    main.chmod(main.stat().st_mode | 0o111)
    for binary in sorted(app.rglob("*.dylib")):
        binary.chmod(binary.stat().st_mode | 0o111)
        run("codesign", "--force", "--sign", identity, "--timestamp=none", binary)
    for framework in sorted(
        app.rglob("*.framework"), key=lambda p: len(p.parts), reverse=True
    ):
        metadata = plistlib.loads((framework / "Info.plist").read_bytes())
        binary = framework / metadata["CFBundleExecutable"]
        binary.chmod(binary.stat().st_mode | 0o111)
        run("codesign", "--force", "--sign", identity, "--timestamp=none", framework)
    run(
        "codesign",
        "--force",
        "--sign",
        identity,
        "--entitlements",
        entitlements,
        "--generate-entitlement-der",
        "--timestamp=none",
        app,
    )
    run("codesign", "--verify", "--deep", "--strict", "--verbose=2", app)


def install(args):
    for tool in (
        "codesign",
        "security",
        "openssl",
        "xcodebuild",
        "xcrun",
        "unzip",
        "zip",
    ):
        if not shutil.which(tool):
            raise ValueError(
                f"missing {tool}; install full Xcode and select it with xcode-select"
            )
    source, output = args.input.resolve(strict=True), args.output.resolve()
    if source == output:
        raise ValueError("signed output must differ from input")
    platform = args.platform
    prefix = platform.upper()
    sdk = "iphoneos" if platform == "iOS" else "appletvos"
    with tempfile.TemporaryDirectory(prefix="maxtube-install-") as temporary:
        work = Path(temporary)
        package = work / "package"
        app = extract_ipa(source, package)
        info_path = app / "Info.plist"
        info = plistlib.loads(info_path.read_bytes())
        expected = "iPhoneOS" if platform == "iOS" else "AppleTVOS"
        if expected not in info.get("CFBundleSupportedPlatforms", []):
            raise ValueError(f"expected a {expected} IPA")
        if list(app.rglob("*.appex")) or list(app.glob("Watch/*.app")):
            raise ValueError(
                "embedded extensions/watch apps require separate provisioning; "
                "use the MaxTube packager to remove them first"
            )
        devices = device_json(work, "list", "devices")["devices"]
        device = select_device(
            devices, platform, os.environ.get(prefix + "_DEVICE_ID", "")
        )
        apps = device_json(work, "device", "info", "apps", "--device", device)["apps"]
        bundle = select_bundle(
            apps,
            platform,
            info["CFBundleIdentifier"],
            os.environ.get(prefix + "_BUNDLE_ID", ""),
        )
        team = os.environ.get(prefix + "_TEAM_ID") or signing_team()
        print(f"{platform}: device {device}, team {team}, bundle {bundle}", flush=True)
        project_root = work / "Provisioning"
        shutil.copytree(ROOT / "Tools/TVOSProvisioning", project_root)
        project = project_root / "MaxTubeProvisioning.xcodeproj"
        if platform == "iOS":
            path = project / "project.pbxproj"
            path.write_text(
                path.read_text()
                .replace("appletvos", "iphoneos")
                .replace(
                    "TARGETED_DEVICE_FAMILY = 3;", 'TARGETED_DEVICE_FAMILY = "1,2";'
                )
                .replace("TVOS_DEPLOYMENT_TARGET", "IPHONEOS_DEPLOYMENT_TARGET")
            )
            path = project_root / "Info.plist"
            path.write_text(
                path.read_text().replace(
                    "TVOS_DEPLOYMENT_TARGET", "IPHONEOS_DEPLOYMENT_TARGET"
                )
            )
        derived = work / "DerivedData"
        try:
            run(
                "xcodebuild",
                "-project",
                project,
                "-scheme",
                "MaxTubeProvisioning",
                "-configuration",
                "Debug",
                "-destination",
                f"platform={platform},id={device}",
                "-derivedDataPath",
                derived,
                "-allowProvisioningUpdates",
                "-allowProvisioningDeviceRegistration",
                "-quiet",
                f"DEVELOPMENT_TEAM={team}",
                f"PRODUCT_BUNDLE_IDENTIFIER={bundle}",
                "build",
            )
        except subprocess.CalledProcessError:
            raise ValueError(
                "Xcode provisioning failed. Check the error above; if login was rejected, "
                "sign back in under Xcode → Settings → Accounts, then rerun this command."
            ) from None
        bootstrap = derived / f"Build/Products/Debug-{sdk}/MaxTubeProvisioning.app"
        profile = plistlib.loads(
            run(
                "security",
                "cms",
                "-D",
                "-i",
                bootstrap / "embedded.mobileprovision",
                capture_output=True,
            ).stdout
        )
        validate_profile(profile, bundle, team, device)
        print(f"Profile expires: {profile['ExpirationDate']} UTC", flush=True)
        info["CFBundleIdentifier"] = bundle
        info["CFBundleDisplayName"] = os.environ.get(
            "APP_DISPLAY_NAME", "YouTube" if platform == "iOS" else "MaxTube"
        )
        info.pop("ITSDRMScheme", None)
        info_path.write_bytes(plistlib.dumps(info, fmt=plistlib.FMT_BINARY))
        sign_app(app, bootstrap, work)
        output.parent.mkdir(parents=True, exist_ok=True)
        staged = work / "signed.ipa"
        run("zip", "-qry", staged, "Payload", cwd=package)
        shutil.copyfile(staged, output)
        if not args.sign_only:
            run(
                "xcrun",
                "devicectl",
                "device",
                "install",
                "app",
                "--device",
                device,
                app,
            )
            run(
                "xcrun",
                "devicectl",
                "device",
                "process",
                "launch",
                "--device",
                device,
                "--terminate-existing",
                bundle,
            )
            run(
                "xcrun",
                "devicectl",
                "device",
                "info",
                "apps",
                "--device",
                device,
                "--bundle-id",
                bundle,
            )
        print(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("platform", choices=["iOS", "tvOS"])
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--sign-only",
        action="store_true",
        help="save signed IPA without installing or launching",
    )
    args = parser.parse_args()
    try:
        install(args)
    except (
        ValueError,
        OSError,
        subprocess.CalledProcessError,
        zipfile.BadZipFile,
    ) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
