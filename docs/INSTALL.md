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
removes the base app's model allowlist, so it can be signed for Apple TV HD and
supported Apple TV 4K hardware. Pick the video decoder build for your model.

## Choose the Apple TV video decoder

The tvOS artifact name ends in the decoder setting it was built with:
`MaxTube_tvOS_*_hardware.ipa`, `MaxTube_tvOS_*_auto.ipa`, or
`MaxTube_tvOS_*_h264.ipa`.

| Setting | What it does |
| --- | --- |
| `hardware` (default) | Applies MuTube's HDR patches: YouTube skips its VP9 hardware decoder check, allows VP9 4K60, and always requests HDR and frame rate display switching. |
| `auto` | Keeps YouTube's own check. With a VP9 hardware decoder, VP9 plays up to 1440p, or 4K at 30 fps. Without one, VP9 is limited to 720p, or 1080p at 30 fps, and other streams use H.264. HDR VP9 is offered only when tvOS reports the device eligible for HDR playback. |
| `h264` | Keeps YouTube's own check, but reports VP9 as unsupported, so YouTube plays H.264 up to 1080p. Only VP9 HDR, which tvOS offers only to HDR-capable devices, can still play. |

| Model | Identifier | Chip | Setting | Status |
| --- | --- | --- | --- | --- |
| Apple TV HD | `AppleTV5,3` | A8 | `h264` | Verified on tvOS 26.6: videos play as H.264 (`avc1`). With `hardware`, video lagged, stuttered, and showed artifacts. |
| Apple TV 4K (1st generation) | `AppleTV6,2` | A10X | `hardware` | Not tested. Use `auto` or `h264` if video lags. |
| Apple TV 4K (2nd generation) | `AppleTV11,1` | A12 | `hardware` | Not tested. Use `auto` or `h264` if video lags. |
| Apple TV 4K (3rd generation) | `AppleTV14,1` | A15 | `hardware` | MuTube upstream tested 4K HDR playback. |

Choose the setting with the `video_decoder` input of **Create MaxTube tvOS
app**, the `tvos_video_decoder` input of **Publish multi-platform MaxTube
release**, or `TVOS_VIDEO_DECODER` for a local build.

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

For Apple TV HD, add `TVOS_VIDEO_DECODER=h264` before `just package-tvos`.

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
- **Video lags, stutters, or shows artifacts on Apple TV:** rebuild with the
  `h264` video decoder; see the decoder table above.
- **Different app appears instead of updating:** reuse the same
  `TVOS_BUNDLE_ID` so tvOS recognizes the installation as the same app.
