# Audit: web font pipeline (WOFF2 → Brotli → OTS) — CLEAN, with one structural finding

*Part of the negative-results registry. Pins: Chromium @ 39c0f061 (2026-11-04), OTS @ 46bea98 (Chromium DEPS pin), HarfBuzz @ 12ee77ee (2026-10-04), FreeType @ a5877f48 (2026-10-17).*

## Why this cone

`@font-face` with a webfont URL is zero-gesture, zero-permission, ad-iframe-reachable, and the bytes come from the attacker's server. The pipeline that turns them into a usable typeface decompresses (WOFF2/Brotli), sanitizes (OTS), and re-serializes (OTS) — historically a rich source of memory bugs. We line-audited the whole path.

## The sanitizers themselves: clean

- **WOFF2** — the vendored revision *is* the 2026-04 integer-wraparound fix ("2018-era library" folklore: refuted; this pin is current). Decoder line-audited: hard limits (128 MB decompressed, 100:1 ratio), table reconstruction bounded.
- **Brotli** — decoder line-audited at its 2026-03 pin: exact-match output sizing, ring-buffer math guarded.
- **OTS** — every table sanitizer read: bounds-validated reads, bounded reserialization. The known CFF1 BCD-operand charset bypass (upstream crbug 505807063) is fixed in Chromium by a **local patch** (`third_party/ots/patches/0001-cff-bcd-operands.patch`) — the upstream OTS fix is *not* in the pinned revision. **Roll hazard**: if OTS ever rolls forward and the local patch drops without checking, the bypass returns.

## The structural finding: Blink deliberately passes 20 tables through unsanitized

`web_font_decoder.cc` marks these tags `TABLE_ACTION_PASSTHRU` — **no OTS validation, verbatim copy into the sanitized font**:

```
CBDT CBLC COLR CPAL CFF2 sbix STAT
BASE GDEF GPOS GSUB avar cvar fvar gvar HVAR MVAR VVAR
```

For several of these, OTS *has* sanitizers — dead code in Chrome. The code comment says it outright: *"Let HarfBuzz handle how to deal with broken tables."* The memory-safety contract for arbitrary `GSUB`/`GPOS`/`GDEF`/`gvar`/`CFF2` bytes is thus delegated to the consumers.

## Who actually consumes those bytes (the consumer map)

Verified at the pin — this is where the story gets good for defenders:

- **HarfBuzz** shapes with GSUB/GPOS/GDEF and reads variation tables and CFF2 metrics — **on every platform, in the renderer**. It receives the raw passthru bytes. It is *designed* for untrusted input (offsets checked at sanitize time, operation budgets, recursion guards — all verified in `hb-sanitize.hh`), but it is the **last big C++ parser standing in the webfont path**.
- **FreeType** is mostly *out* of the webfont path now: Linux/Android/ChromeOS webfonts go through **Fontations (Rust)**; Mac/Windows go through CoreText/DirectWrite. A pre-audit fear ("FreeType parsing webfonts on Android = WebView multiplier") turned out to describe the pre-migration world.
- **Fontations/skrifa** owns the color/CFF2/glyf rendering parse on Linux/Android — memory-safe by construction.

## Known-bug archaeology (are we already dead in the water?)

We triaged the full delta between Chrome's pinned HarfBuzz and upstream main (327 commits; ~29 security-flavored), plus FreeType's 13-commit delta:

- **Zero known memory-safety fixes are live in Chrome's pins.** Every candidate either doesn't touch the shaping path (subsetter-only, paint-API-only, platform-specific) or degrades to a logic fix.
- One genuine **shaping infinite loop** (GPOS cursive-attach cycles) is live in the pin: attacker font → renderer hang, zero gestures, DoS-class (VRP-excluded). Fixed upstream 2026-10-30 with a public test font; Chrome's roll just hasn't landed. Reproducible in Canary today with the upstream test font.
- Several delta fixes credit "Anthropic's OSS Scanner" — automated miners are working this exact history. Independent auditors are not alone, and not first.

## Verdict

**Clean** — no VRP-class finding in the pipeline itself. But the audit's real output is the map above: **HarfBuzz's layout engine is the last large C++ consumer of raw attacker font bytes in Chrome's webfont path, and Blink's own source documents the delegation.** That's where the remaining unknown-bug risk concentrates, and where any follow-up should dig (GSUB/GPOS/GDEF apply machinery, variation-store math, CFF2 extents — all against the "arbitrary bytes" assumption rather than the "OTS-sanitized" one).
