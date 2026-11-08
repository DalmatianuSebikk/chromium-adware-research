# Further directions — where to dig next

*The map of what this project did NOT finish. If you pick up any of these, read [`WHY-THIS-RESEARCH.md`](WHY-THIS-RESEARCH.md) and [`DELIVERY-BAR.md`](DELIVERY-BAR.md) first. Everything below is graded by the delivery bar.*

## Un-audited cones that ads can reach

1. **HarfBuzz layout engine** — the #1 remaining C++ cone, by elimination rather than enthusiasm. Blink passes 20 font tables (`GSUB GPOS GDEF gvar CFF2 COLR …`) to HarfBuzz *unsanitized by design* (see [`audits/WEBFONT-PIPELINE.md`](../audits/WEBFONT-PIPELINE.md)); HB shapes them in the renderer on every platform. The known-bug delta is clean in Chrome's pins (we triaged all 327 commits), so what remains is a line-audit for *unknown* bugs in the apply machinery (`hb-ot-layout-common.hh`, `hb-ot-layout-gsubgpos.hh`, ~13k lines) and the variation-store math, under the "arbitrary bytes" assumption HB is built for. Caveat: automated scanners are visibly mining this library's history — assume the clock runs.
2. **WebTransport + QUIC client** (`third_party/blink/renderer/modules/webtransport/`, network service) — attacker-chosen server responses over a modern transport with lots of state-machine surface. The AdFection SDK probed for WebTransport availability (`WebTransport` in its capability list), which tells you attackers care.
3. **Chunked-delivery fuzzing harness for image decoders** — Chrome's own image fuzzers feed whole buffers; the streaming seam (bytes in attacker-chosen slices/timings) is comparatively unexercised. We specified the harness (delivery strategies + ASAN oracle) in our notes; building it is the follow-up ([`audits/IMAGE-FAMILY-2.md`](../audits/IMAGE-FAMILY-2.md)).

*(The cones that used to lead this list — GIF, PNG, JPEG, WebP, JXL/AVIF, the multipart re-feeder, the MSE demuxers, the webfont sanitizers — are now audited clean; see `audits/`.)*

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
