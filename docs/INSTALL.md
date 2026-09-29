# Installing MaxTube

GitHub releases contain unsigned IPAs. Every user must sign an IPA with their
own Apple account before installation. The published binary is identical until
that account-specific signature and bundle identifier are applied.

## Choose the artifact

| Device | Release artifact | Minimum system |
| --- | --- | --- |
| iPhone | `MaxTube_iOS-iPadOS_*.ipa` | iOS 15.0 or the base IPA minimum |
| iPad | `MaxTube_iOS-iPadOS_*.ipa` | iPadOS 15.0 or the base IPA minimum |
| Apple TV | `MaxTube_tvOS_*.ipa` | The base IPA minimum; current verified base is tvOS 13.0 |

The Apple TV build is verified on Apple TV HD with tvOS 26.6. Its packager
removes the base app's model allowlist, so the same artifact can be signed for
Apple TV HD and supported Apple TV 4K hardware.

## Free Apple account

Apple permits personal on-device testing without a paid Developer Program
membership. Sign into **Xcode → Settings → Accounts** once with the Apple
account. Xcode calls this a Personal Team.

Apple's current Personal Team limits are:

- 10 active App IDs, each valid for seven days;
- three registered test devices per platform, each valid for seven days; and
- provisioning profiles that expire after seven days.

Consequently, a free-account installation must be signed and installed again
at least every seven days. These limits come from Apple's
[membership comparison](https://developer.apple.com/support/compare-memberships/).

### iPhone and iPad

1. Enable Developer Mode on the device and connect it to the Mac once.
2. Download `MaxTube_iOS-iPadOS_*.ipa` from the GitHub release.
3. Use an IPA sideloading tool that signs with the user's Apple account, select
   the connected device, and install the IPA.
4. Repeat the signing/installation before the seven-day profile expires.

The signing tool must preserve support for both device families and sign any
embedded extension as well as the main app. A paid signing certificate is not
required for personal use.

### Apple TV

Prerequisites:

- macOS with the full Xcode installation;
- the Apple account configured once in Xcode;
- `just` installed;
- Developer Mode enabled on the Apple TV; and
- the Apple TV paired with the Mac through Xcode's Devices window.

From the repository root, run:

```sh
just install-tvos /path/to/MaxTube_tvOS.ipa
```

The command automatically:

1. detects the Apple Development team and the single paired physical Apple TV;
2. asks Xcode CLI to register the device and refresh a profile;
3. re-signs the app and nested Swift library;
4. writes `dist/MaxTube-tvOS-signed.ipa`;
5. installs the app with `devicectl`; and
6. launches MaxTube.

If the Mac has multiple Apple development teams or paired Apple TVs, select
them explicitly:

```sh
TVOS_TEAM_ID=ABCDE12345 \
TVOS_DEVICE_ID=0000000000000000000000000000000000000000 \
TVOS_BUNDLE_ID=com.example.maxtube.tvos \
  just install-tvos /path/to/MaxTube_tvOS.ipa
```

Rerun the same command to renew a free seven-day profile. App data is retained
when the bundle identifier remains unchanged.

## Paid Apple Developer Program

The installation steps are the same. A paid development profile normally lasts
one year instead of seven days and supports the broader device-registration and
distribution options described by Apple. Xcode automatic signing registers the
connected device and refreshes the profile; Apple documents this process in
[Distributing your app to registered devices](https://developer.apple.com/documentation/xcode/distributing-your-app-to-registered-devices).

For Apple TV, use the same one-command installer:

```sh
just install-tvos /path/to/MaxTube_tvOS.ipa
```

## Build locally from a decrypted base

MaxTube does not download a YouTube base IPA.

For iPhone and iPad:

```sh
just build-enhancer
just package /path/to/YouTube.ipa dist/ytkace.deb
```

For Apple TV 4.54.01:

```sh
DEVELOPER_DIR=/Applications/Xcode-27.0.0.app/Contents/Developer \
  just package-tvos /path/to/YouTube-tvOS-4.54.01.ipa
```

Then sign/install the resulting IPA using the applicable section above.

## Troubleshooting

- **No Apple Development team detected:** add the Apple account in Xcode once,
  or set `TVOS_TEAM_ID` explicitly.
- **More than one Apple TV detected:** set `TVOS_DEVICE_ID` to the intended
  device UDID.
- **Profile expired:** rerun `just install-tvos`; Personal Team profiles expire
  after seven days.
- **Device is unavailable:** wake the Apple TV, keep it on the same network,
  and confirm that it remains paired.
- **Different app appears instead of updating:** reuse the same
  `TVOS_BUNDLE_ID` so tvOS recognizes the installation as the same app.
