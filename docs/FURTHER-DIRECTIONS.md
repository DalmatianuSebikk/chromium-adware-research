# Further directions — where to dig next

*The map of what this project did NOT finish. If you pick up any of these, read [`WHY-THIS-RESEARCH.md`](WHY-THIS-RESEARCH.md) and [`DELIVERY-BAR.md`](DELIVERY-BAR.md) first. Everything below is graded by the delivery bar.*

## Un-audited cones that ads can reach

1. **GIF decoder** (`third_party/blink/renderer/platform/image-decoders/gif/`) — same vintage and shape as the ICO/BMP decoders we audited clean (see [`audits/IMAGE-DECODERS.md`](../audits/IMAGE-DECODERS.md)). LZW streaming, interlacing, frame composting — several classic bug shapes. The write primitive downstream (`ImageFrame::SetRGBA`) has **no release-mode bounds check**, so any coordinate slip anywhere in the reader is immediately an OOB write. This is the highest-value remaining cone in the image family.
2. **PNG decoder proper** — our ICO audit found the container hands PNG-in-ICO decoders *more bytes than the entry owns* (spec confusion, currently harmless). libpng itself is heavily audited, but Chromium's APNG/metadata glue is worth a pass.
3. **Multipart image re-feed parser** (`multipart_image_resource_parser.cc`) — the feed mechanism itself: unbounded header buffering, decoder state that never resets between parts. An attacker-controlled server can re-feed an image decoder a chosen byte stream in chosen slices and timings. We audited what the decoders do with the bytes; we did not finish auditing the re-feeder.
4. **WebTransport + QUIC client** (`third_party/blink/renderer/modules/webtransport/`, network service) — attacker-chosen server responses over a modern transport with lots of state-machine surface. The AdFection SDK probed for WebTransport availability (`WebTransport` in its capability list), which tells you attackers care.

## Method-level approaches (different from line-by-line reading)

5. **Patch archaeology** — mine git history of a chosen cone for *silent fixes*: commits that fix a lifetime/race/bounds issue without a CVE, a test, or a bug reference, especially in the 2024–2026 window (the AdFection infections were 2024–2025). A silent fix is a burned 0-day; the *absence* of one in a vulnerable-shaped function means it may still be live.
6. **Variant hunting off public postmortems** — take each public Chromium exploit write-up (CVE-2023-4863 libwebp, the historical Candiru/V8 chains, etc.), extract the *shape* of the bug, and grep the current tree for the same shape elsewhere. Cheap, mechanical, and historically productive.
7. **DCHECK-oracle fuzzing** — build with `dcheck_always_on` and fuzz: compiler-inserted invariant checks become free crash oracles that don't exist in release builds. We validated the pipeline (see [`audits/NEGATIVE-RESULTS.md`](../audits/NEGATIVE-RESULTS.md)); pointing it at Blink (not just V8) is unexplored.

## The structural asymmetries (no inner bug needed to be interesting)

8. **Android WebView** — single renderer for the whole embedded browser, no OOPIFs between iframes, and legacy JS-bridge surfaces (`addJavascriptInterface` / GinJavaBridge origin matching) that connect renderer compromise to app compromise. Every renderer finding is worse here. A dedicated WebView-shaped threat model document would be a genuine public contribution.
9. **Recon surfaces** — the targeting stage of an ad attack needs identity+location: WebRTC srflx IP leak (zero permission), header enrichment interplay (MSISDN), cookie-sync graph edges. None of these need memory corruption; auditing them is privacy research with security framing. Citizen Lab's pending "DARK CARTOGRAPHER" report will move this from side-note to center.

## Outside the renderer entirely

10. **Network service & Mojo IPC** — the browser-side processes that parse what the network hands them. Not ad-frame-reachable directly, but the ad server *is* the network peer; attacker-chosen responses flow through network-service parsing (HTTP/2, QUIC, HPACK, header enrichment proxies).
11. **The bundled third-party library family** — libwebp (post-4863), freetype, harfbuzz, dav1d, libyuv, pdfium. Each has its own CVE history and its own fuzzing coverage gaps. The AdFection exploit stage, wherever it lived, lived *somewhere* in this stack.
12. **Detection, not exploitation** — the inverse problem: how could an ad platform *detect* that one of its slots is carrying per-viewer-divergent code? (Answer today: it structurally can't — the creative fetch carries the viewer's own IP.) A rigorous write-up of *why* scanner-proof delivery works, and what platform change would break it, is arguably more publishable than another clean-audit verdict.

## What we'd tell our past selves

Spend less time on cones Google visibly fuzzes (V8 core, libpng), more time on **cones whose tests are thin** (image *container* logic, multipart glue, WebView bridges) and on **methods that scale** (patch archaeology, DCHECK oracles). And write the negative results down as carefully as the positives — they're what told us where the armor actually is.
