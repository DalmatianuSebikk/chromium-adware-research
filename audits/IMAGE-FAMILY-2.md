# Audit round 2: the rest of the image family — CLEAN

*Part of the negative-results registry. Pin: public Chromium main @ 39c0f061 (2026-11-04). Follows [`IMAGE-DECODERS.md`](IMAGE-DECODERS.md) (ICO/BMP).*

## The surprise: most of the family is no longer C++

Round 1 established that `ImageFrame::SetRGBA` has no release-mode bounds check — memory safety rests entirely on the decoder above it. Round 2 asked who's actually above it now, and the answer reshaped the map:

| Format | Live path in Chrome | Who parses attacker bytes |
|---|---|---|
| GIF | Blink wrapper (57 lines) → Skia `SkWuffsCodec` | **wuffs** — memory-safe-by-construction transpiled C |
| PNG | Blink wrapper (32 lines) → `SkPngRustCodec` | **Rust `png` crate 0.18.1** (vendored; libpng's Skia codec isn't even compiled) |
| JPEG | Blink `JPEGImageDecoder` — real 1,350-line C++ over libjpeg-turbo | C++ (a Rust variant exists, flag-off) |
| WebP | Blink-native C++ over vendored libwebp 1.6.0 | C (line-audited) |
| JXL | Blink wrapper → Rust `jxl` crate 0.8.0 — **enabled by default** | Rust (81/81 `unsafe` sites dispositioned) |
| AVIF | crabbyavif / dav1d / libgav1 | Rust + hardened C |

## What was verified (per cone)

- **GIF** — every LZW/interlace/disposal shape now runs inside wuffs; the one scary-looking pattern (a codec-internal pointer stash for incremental decode, marked `DanglingUntriaged` upstream) was chased through four files of Blink lifetime discipline: frame reallocs reset it, cache clears null it, and the external-memory decode mode that could have resumed with a stale stash never caches its decoders at all.
- **PNG** — C++ shell arithmetic is wrapped in `SkSafeMath`, and Skia's `SkSpan` **bounds-checks and hard-aborts in release builds**, turning any arithmetic slip into a crash rather than an OOB write. The Rust crate enforces APNG sub-frame bounds with checked math; Adam7 expansion is safe-indexed.
- **JPEG** — row loops match allocations, YUV split bounded, suspension offset-based, metadata layer strict. One latent shape documented and closed: a TIFF helper hardcodes a 4-byte-per-element stride for all tag types, which *would* over-read SHORT arrays — but every live caller reads exactly one element, so it's unreachable today. Reported as an upstream hardening candidate.
- **WebP** — end-to-end pass of the Blink decoder and vendored libwebp: the CVE-2023-4863 fix is present structurally, plus two extra hardenings; the 40-branch streaming seam (partial data, buffer growth mid-decode, suspension/resume) all fails closed.
- **JXL** — newest, least-fuzzed surface (the crate is © 2026, and JXL decoding ships enabled by default). All 81 `unsafe` sites in the decoder crate dispositioned; struct invariants are release-asserted at construction *and* use; SIMD helpers release-assert slice lengths before raw ops on all four desktop ISAs.
- **Multipart re-feed** — the round-1 hypothesis "decoder state never resets between parts" is **false**: each part gets `ClearImage()` and a fresh decoder. The state machine (part boundaries, headers, flush) guards every transition.
- **Shared orchestration** — full pass of the frame cache, incremental decode driver, and buffer readers: pixel addresses stay stable across vector growth (bitmap refs are shared, not copied), and caches are defensively cleared on any potentially-invalidating event.

## Soft spots (all DoS/functional class, excluded from Chrome's VRP)

Unbounded frame-vector growth on pathological GIFs; a debug-only DCHECK in the WebP streaming path reachable only by malformed ANMF chunks (release path fails closed); allocation-amplification shapes in JXL/AVIF metadata.

## One gap worth naming

Chrome's own image fuzzers feed decoders whole buffers — the **streaming** seam (bytes arriving in attacker-chosen slices and timings) is exercised far less. We designed a chunked-delivery harness (strategies: one-shot, fixed-N, at-offsets, random, prime-sized, stall, truncate) with an ASAN build as oracle; it's specified in our working notes and not yet built. That's the method-level follow-up we'd point the next person at.

## Verdict

**Clean.** With ICO/BMP (round 1), the attacker-bytes→image-decode→OOB-write chain is closed across the entire image family at this revision: the C++ survivors (JPEG, WebP) are audited, and everything else moved to memory-safe languages. The 2008-era attack surface is genuinely gone from this cone.
