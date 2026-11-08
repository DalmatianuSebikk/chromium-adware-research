# Audit: MSE media demuxers (MP4/WebM/MP2T/MPEG/HLS) — CLEAN

*Part of the negative-results registry. Pin: public Chromium main @ 39c0f061 (2026-11-04). Cone: `media/formats/` + `media/filters/`.*

## Why this cone

`MediaSource.appendBuffer()` hands *attacker-authored container bytes* (from the page's own JS — an ad iframe qualifies) to pure Chromium C++ parsers. And the mercenary precedent is media-heavy: Candiru's known Chrome 0-days were 2/3 in media subsystems. Box parsers, track assembly, sample tables — decades of fuzzer attention, but also decades of surface.

## What was verified

- **MP4 box tree** (moov/trak/mdat/stbl/stsd/stsz/stco/stss/…): size arithmetic is span-based and `RCHECK`-hardened throughout; offsets validated against buffer extents before use; recursive descent bounded.
- **WebM/Matroska EBML**: variable-length int parsing bounded; unknown elements skipped with checked sizes; block/simpleblock sample extraction bounds-checked.
- **MPEG-TS (mp2t)** and **MPEG-PS**: PID/PMT parsing, PTS/DTS math, packet continuity — guarded; the TS demuxer is now shipping in desktop stable, which raises its reach.
- **HLS playlists** (M3U8): attribute parsing bounded; the demuxer is desktop-stable now.
- **Chunk demuxer state machine** (the `appendBuffer` orchestrator): every append/flush/seek transition checked against stream state.

All told: **no VRP-qualifying memory-safety finding** in the cone.

## Two notes worth keeping

1. **A crash-only null deref, upstreamable**: in `track_run_iterator.cc`, a `senc` box on a track with handler `'meta'` can reach `default_iv_size` with a null encryption config (the `index == 0` ternary reads it unguarded). Null deref = excluded from Chrome's VRP by policy (≤ DoS), but it's a real robustness bug; worth an upstream patch.
2. **A 256 MiB transient allocation** in the ESDS (MPEG-4 descriptor) path on crafted input — allocation-amplification class, capped, DoS-only.

## Coverage honesty

The NALU extractors (H.264/H.265 bitstream parsers behind the demuxers) and `audio_video_metadata` were interface-checked, not line-audited. If someone extends this cone, that's where to start.
