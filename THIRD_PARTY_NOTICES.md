# Third-party notices

## YTKACE

MaxTube builds YTKACE revision
`c689f330cd4419865ce077cdd7189cbe80bb56c7` from
<https://github.com/itzzace/ytkace>.

MIT License

Copyright (c) 2026 YTKACE contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Components documented by YTKACE

The following notices are copied from the pinned YTKACE release.

YTKACE source is licensed under MIT. The following components and services have separate terms.

### FFmpeg

YTKACE statically links FFmpeg 8.1.2 for local media processing. It is built from the official release tarball by `Scripts/build-ffmpeg.sh`, without `--enable-gpl` and without `--enable-nonfree`, so the result is LGPL only. Licence texts ship in the repository at `Vendor/FFmpeg/COPYING.LGPLv2.1` and `COPYING.LGPLv3`. See https://ffmpeg.org/legal.html.

### SponsorBlock and DeArrow

SponsorBlock and DeArrow community data is provided by the SponsorBlock service under CC BY-NC-SA 4.0. See https://sponsor.ajay.app/. The shield image shipped in `YTKACE.bundle` is SponsorBlock's artwork, taken from the same site and used to mark the integration.

### AiSList

Hide AI Channels uses the AiSList blocklist and warnlist from [aisloplist.com](https://aisloplist.com), maintained by the AiSList community at [Override92/AiSList](https://github.com/Override92/AiSList) and licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). The lists are downloaded unmodified and only read to match channels in the feed and search. The list locations and the idea of matching channel handles in feed data came from the [Morphe](https://github.com/MorpheApp/morphe-patches) AiSList patch. No Morphe code is used.

### SABR reference

The download path implements YouTube's SABR streaming protocol. It was written for YTKACE, developed against an iPad on iOS 16. Protocol understanding came in part from reading [LuanRT/googlevideo](https://github.com/LuanRT/googlevideo), an MIT-licensed library implementing UMP and SABR. No code from that project is included.

### YTPlaybackFix

The playback error recovery in `Tweak/Features/Playback/PlaybackFixHooks.mm` is adapted from [YTPlaybackFix](https://github.com/Mark02-2012/YTPlaybackFix) by Mark02, used under the MIT licence. It is his `Refresh.xm` method: intercept `handleError:` for playback error codes 14 and 0, send a `YTPlayerTapToRetryResponderEvent`, seek back to the last known position, and re-check after a second. The overall control flow is his. Changes here: the port off Logos to the runtime hooking used elsewhere, the preference gate and the logging; recovery now reloads only the player through `player:reloadWithContext:`, falling back to his retry event when that is unavailable, since the retry event reloads the whole watch page; the re-check waits three seconds instead of one, so a reload still in progress is not retried a second time; and the replay step was dropped because the selector no longer exists. The full licence text is reproduced in the header of that file.

MIT License, Copyright (c) 2026 Mark02.

### yt-dlp EJS challenge solver

`Resources/YTKACE.bundle/ejs/yt.solver.core.min.js` and `yt.solver.lib.min.js` are the JavaScript challenge solver from [yt-dlp/ejs](https://github.com/yt-dlp/ejs), release 0.8.0, used unmodified by `Tweak/Features/Playback/ChallengeSolver.mm` to compute the `n` parameter of TV client stream URLs from YouTube's player script. The solver is released under the Unlicense. The library bundle includes [meriyah](https://github.com/meriyah/meriyah) (ISC License, Copyright (c) 2019 and later, KFlash and others) and [astring](https://github.com/davidbonnet/astring) (MIT License, Copyright (c) 2015, David Bonnet); their licence texts are reproduced in the header of that file.

### TV client identifiers

`Tweak/Features/Streaming/TVClient.mm` requests streams as YouTube's TV client. The client name, version, device fields and user agent it sends, and the order of requests (a visitor ID from `/guide`, then `/player` with the player's signature timestamp), follow the values and approach published by the [Morphe](https://github.com/MorpheApp/morphe-patches) project. No Morphe code is used.

### visionOS client identifiers

`Tweak/Features/Streaming/HLSPlayback.mm` and `Tweak/Features/Downloads/DirectDownloader.mm` request streams as YouTube's visionOS client. The client name, version, device and OS fields and user agent they send are the values published by [yt-dlp](https://github.com/yt-dlp/yt-dlp), which is released under the Unlicense. No yt-dlp code is used.

### YTLiquidGlass

The Liquid Glass tab bar and top bar in `Tweak/Features/Navigation/TabBarHooks.mm` and `GlassChrome.mm` build on ideas from [YTLiquidGlass](https://github.com/UltraGeek0102/YTLiquidGlassEXTRA) by UltraGeek0102, used with permission: fading YouTube's own tab bar background instead of removing it, selecting tabs through the pivot bar controller, and placing glass behind the top right buttons, search bar and header buttons. The code here was written for YTKACE.

### LiquidLens

The tab bar selection lens uses UIKit's private `_UILiquidLensView`. How to create and drive it was learned from [Livsy90/LiquidLens](https://github.com/Livsy90/LiquidLens), a research demo released under the MIT licence. No code from that project is included.

### Apple frameworks

YTKACE uses UIKit, AVFoundation and SF Symbols supplied by iOS. SF Symbols artwork is requested at runtime and is not included as a redistributed asset pack.

## MuTube

The tvOS package job downloads MuTube revision
`ce080721edd30abcda6f3a67acab0be142067e6a` from
<https://github.com/Exaphis/mutube>. The runtime injection payload in
`Resources/mutube-inject.js` is derived from that revision.

MuTube does not publish a license. Its copyright holder has therefore not
provided an explicit redistribution license. This private fork knowingly
accepts that risk; this notice does not grant rights to publish MuTube or a
derived binary.

## TizenTube

The MuTube payload loads `@foxreis/tizentube` version 1.15.0 from jsDelivr.
TizenTube source is available at <https://github.com/reisxd/TizenTube> under
the GNU General Public License version 3. The package is fetched at runtime
and is not copied into the IPA by this repository.
