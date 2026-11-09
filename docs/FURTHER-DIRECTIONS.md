# Further directions — where to dig next

*The map of what this project did NOT finish. If you pick up any of these, read [`WHY-THIS-RESEARCH.md`](WHY-THIS-RESEARCH.md) and [`DELIVERY-BAR.md`](DELIVERY-BAR.md) first. Everything below is graded by the delivery bar.*

## Un-audited cones that ads can reach

*Ranked by the [`COVERAGE-MAP.md`](COVERAGE-MAP.md) chain-stage analysis — the cones below are the chain stages nobody here has examined yet.*

1. **Network-response parsers** (`//net`: HTTP/2/nghttp2, HPACK, in-tree QUIC, Content-Encoding decoders for gzip/zlib/zstd) — in the AdFection model the ad server *is* the network peer and owns every response byte; this is the largest never-touched surface on the map. Heavily Google-fuzzed — the honest expectation is "armored," but the map should say so with evidence.
2. **WebGL/ANGLE** — the AdFection SDK's own probe list asked for `WebGL`; shader/buffer/texture bytes are attacker-controlled in any ad frame, and this is the biggest untouched *renderer* surface (shader translation → Metal on macOS). Historically one of the richest CVE surfaces in the renderer.
3. **ffmpeg + H.264/H.265 NALU decode paths** — video ads are the in-app medium (76.7% of AdFection impressions); the demuxers in front are audited clean but the codec interiors behind them are not.
4. **WebTransport + QUIC client** (`third_party/blink/renderer/modules/webtransport/`, network service) — the AdFection SDK probed for WebTransport availability, which tells you attackers care.
5. **HarfBuzz — remaining interior** — the apply-machinery core (matchers, Rule/Context/ChainContext, accelerators, `layout-common`) is now audited clean; what's left is the GSUB/GPOS lookup-format apply paths and the variation-store math, under the "arbitrary bytes" delegation Blink documents. Caveat unchanged: automated scanners are visibly mining this library's history — assume the clock runs.
6. **Chunked-delivery harness — remaining runs** — the harness is now **built** and its first run came back 138/138 clean (see [`audits/NEGATIVE-RESULTS.md`](../audits/NEGATIVE-RESULTS.md) entry 24); the follow-ups are the hang suite and a DCHECK/ASAN oracle build.

*(The cones that used to lead this list — GIF, PNG, JPEG, WebP, JXL/AVIF, the multipart re-feeder, the MSE demuxers, the webfont sanitizers, the WebCodecs broker, the OOPIF process-swap paths — are now audited clean; see `audits/` and the [`COVERAGE-MAP.md`](COVERAGE-MAP.md) for what that leaves.)*

## Method-level approaches (different from line-by-line reading)

4. **Patch archaeology** — mine git history of a chosen cone for *silent fixes*: commits that fix a lifetime/race/bounds issue without a CVE, a test, or a bug reference, especially in the 2024–2026 window (the AdFection infections were 2024–2025). A silent fix is a burned 0-day; the *absence* of one in a vulnerable-shaped function means it may still be live.
5. **Variant hunting off public postmortems** — take each public Chromium exploit write-up (CVE-2023-4863 libwebp, the historical Candiru/V8 chains, etc.), extract the *shape* of the bug, and grep the current tree for the same shape elsewhere. Cheap, mechanical, and historically productive.
6. **DCHECK-oracle fuzzing** — build with `dcheck_always_on` and fuzz: compiler-inserted invariant checks become free crash oracles that don't exist in release builds. We validated the pipeline (see [`audits/NEGATIVE-RESULTS.md`](../audits/NEGATIVE-RESULTS.md)); pointing it at Blink (not just V8) is unexplored.

## The structural asymmetries (no inner bug needed to be interesting)

7. **Android WebView** — single renderer for the whole embedded browser, no OOPIFs between iframes, and legacy JS-bridge surfaces (`addJavascriptInterface` / GinJavaBridge origin matching) that connect renderer compromise to app compromise. Every renderer finding is worse here. A dedicated WebView-shaped threat model document would be a genuine public contribution.
8. **Recon surfaces** — the targeting stage of an ad attack needs identity+location: WebRTC srflx IP leak (zero permission), header enrichment interplay (MSISDN), cookie-sync graph edges. None of these need memory corruption; auditing them is privacy research with security framing. Citizen Lab's pending "DARK CARTOGRAPHER" report will move this from side-note to center.

## Outside the renderer entirely

9. **Network service & Mojo IPC** — the browser-side processes that parse what the network hands them. Not ad-frame-reachable directly, but the ad server *is* the network peer; attacker-chosen responses flow through network-service parsing (HTTP/2, QUIC, HPACK, header enrichment proxies).
10. **The bundled third-party library family** — libwebp (post-4863), freetype, harfbuzz, dav1d, libyuv, pdfium. Each has its own CVE history and its own fuzzing coverage gaps. The AdFection exploit stage, wherever it lived, lived *somewhere* in this stack.
11. **Detection, not exploitation** — the inverse problem: how could an ad platform *detect* that one of its slots is carrying per-viewer-divergent code? (Answer today: it structurally can't — the creative fetch carries the viewer's own IP.) A rigorous write-up of *why* scanner-proof delivery works, and what platform change would break it, is arguably more publishable than another clean-audit verdict.

## What we'd tell our past selves

The advice we started with ("spend less time on cones Google visibly fuzzes, more on thin-tested container logic") turned out to be half right: the container logic *was* thin-tested, but Google's fix for that was structural, not incremental — the 2008-era image decoders didn't get patched, they got **replaced** (wuffs, Rust, Fontations). So before line-auditing any "legacy" cone, spend a day verifying the legacy code is still *live* — we nearly audited a decoder that isn't compiled, and one of our refuted findings (entry 18) hinged on exactly that mistake. What's left after the structural migrations is a short list: HarfBuzz's layout core, WebTransport, the streaming seams fuzzers don't reach. Dig where the migrations *haven't* landed yet, and write the negative results down as carefully as the positives — they're what told us where the armor actually is.
