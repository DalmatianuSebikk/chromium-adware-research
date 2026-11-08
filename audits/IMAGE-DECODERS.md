# Audit: legacy image decoders (ICO/BMP) — CLEAN

*Part of the negative-results registry. Pin: public Chromium main @ 39c0f061 (2026-11-04). Files audited line-by-line: `bmp_image_reader.cc` (1,067 ln), `bmp_image_reader.h`, `ico_image_decoder.cc` (365 ln), `image_frame.h` (write path), decoder factories, feature flags.*

## Why we audited this

The AdFection feed chain idea: an attacker's **server** sends bytes that a victim's **browser** decodes with 2008-era C++ code. If any coordinate calculation in those decoders slips once, the write lands with no release-mode bounds check (see below) — a one-byte-off bug becomes an out-of-bounds write, the CVE-2023-4863 (libwebp) shape. Image decoding is reachable from a plain ad iframe with zero permissions, so this cone passes the delivery bar by construction.

## What we confirmed first (the good news for an attacker, mostly)

- **The write primitive is unguarded in release builds.** `ImageFrame::SetRGBA(x, y, ...)` computes `bitmap_.getAddr32(x, y)` and writes. In release Chrome there is **no bounds check** on that write — only a debug-build assertion about pixel format. Memory safety rests *entirely* on the decoder code above it never producing a bad coordinate.
- The C++ decoder is the **live path**: a Rust ICO decoder exists behind a feature flag that is disabled by default; BMP has no Rust variant at all.

## What we found

**Every guard is present.** Specifically verified:

- Header validation: dimension caps, the full compression×bit-depth matrix, height sign handling, ICO height-halving.
- Color tables: palette sizes clamped before allocation, truncated palettes handled explicitly, out-of-range palette indexes fall back to a black pixel instead of an OOB read — at *both* call sites (RLE and non-RLE).
- RLE decoding: every escape, delta, and absolute-run mode bounds-checked; malformed runs fail closed.
- Row arithmetic: byte-alignment math for 1/2/4/8-bit rows checked for every bit depth.
- Bitmask formats (nonstandard BMPs): masks validated for size, overlap, and contiguity; the lookup-table slicing arithmetic is exact-fit for every legal bit width.
- Y-coordinate handling in both top-down and bottom-up orientations: no write can occur outside `[0, height)`.
- ICO containers: exact size reconciliation between the directory entry and the decoded image — allocation always at the reconciled size.

**Two soft spots, both harmless to memory safety** (recorded as DoS/spec-conformance class):
1. A 32-bit addition in the "is this frame fully received?" check can wrap on absurd files — worst case a complete image is reported failed. No memory effect.
2. A PNG embedded in an ICO can read bytes past its own directory entry (the decoder hands it the rest of the file); PNG's own decoder bounds-checks internally, so the effect is spec confusion, not corruption.

## Verdict

**Clean.** No coordinate bug exists in this cone at the audited revision. The chain "attacker bytes → image decode → OOB write" is structurally alive in Chrome (the write primitive is genuinely unguarded), but these two decoders are not the way through — and neither, it turned out, is anything else in the image family: see round 2 ([`IMAGE-FAMILY-2.md`](IMAGE-FAMILY-2.md)), where GIF, PNG, JPEG, WebP, JXL and AVIF all came back clean too.

*Why publish a clean audit? Because "where is Chrome NOT armored" requires knowing where it IS. This one cost a full line-by-line pass to establish; now nobody has to repeat it.*
