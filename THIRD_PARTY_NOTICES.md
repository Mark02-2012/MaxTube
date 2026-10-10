# Third-party notices

## YTKACE

MaxTube builds YTKACE revision
`2152278b2f493e56c6192cdeac615062ba91d557` from
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

YTKACE statically links FFmpeg 8.1.2 under the LGPL configuration documented
in its source tree. That tree contains the corresponding LGPL 2.1 and LGPL 3
texts and its FFmpeg build script.

SponsorBlock and DeArrow community data is provided by the SponsorBlock service
under CC BY-NC-SA 4.0. YTKACE's SABR implementation was informed by the
MIT-licensed `LuanRT/googlevideo` project without copying its code. Its playback
recovery is adapted from Mark02-2012/YTPlaybackFix under the MIT license.

For the exact notices, license copies, and build materials associated with the
pinned binary, see the YTKACE source revision identified above.

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
