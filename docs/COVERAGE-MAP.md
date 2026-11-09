# Coverage map — the AdFection chain, cone by cone

*The attack chain from Citizen Lab's AdFection report, stage by stage, against what this project has (and hasn't) verified. This is the "where did we actually look" companion to [`FURTHER-DIRECTIONS.md`](FURTHER-DIRECTIONS.md).*

The chain an ad-delivered attack implies: an attacker-owned ad server wins an auction, its creative/SDK bytes run inside an ordinary ad frame (76.7% of AdFection impressions were in-app WebViews), it probes the environment, and — in the one confirmed wild case — exploited the browser. Each stage names a Chromium code surface. Here's our coverage:

| Chain stage (attacker controls…) | Coverage in this project | Not yet touched |
|---|---|---|
| Ad creative bytes → image decode | ✅ **All 8 image cones** (ICO, BMP, GIF, PNG, JPEG, WebP, JXL, AVIF) + multipart re-feed + decoder orchestration — see `audits/` | — closed |
| Font bytes → webfont/text stack | ✅ WOFF2, Brotli, OTS sanitizers; HarfBuzz known-bug delta (327 commits triaged) + apply-machinery core (`gsubgpos.hh`, `layout-common.hh`, caches) | HarfBuzz GSUB/GPOS lookup-format apply paths + variation-store math (the delegated-to surface — see [`audits/WEBFONT-PIPELINE.md`](../audits/WEBFONT-PIPELINE.md)) |
| Video/audio ads → media stack | ✅ MSE demuxers (MP4/WebM/MP2T/MPEG/HLS), WebCodecs decoder broker | **ffmpeg + H.264/H.265 NALU decode paths** — the in-app video-ad medium, historically one of the richest CVE farms in this stack |
| Attacker server → network responses | — never | **`//net` response-path parsers: HTTP/2, HPACK, QUIC-in-tree, Content-Encoding decoders (gzip/zlib, zstd)** — an ad server owns every response byte; heavily Google-fuzzed but unexamined here |
| SDK environment probes (the AdFection SDK's own capability list) | WebRTC ✅ (parser clean; srflx leak documented as recon-class), WebCodecs ✅ | **WebGL/ANGLE** (shader/buffer/texture bytes — the biggest untouched renderer surface the SDK probed for) · **IndexedDB/LevelDB** · **SharedWorker/serviceWorker lifecycle** · **WebTransport** (the SDK probed for it explicitly) |
| Renderer foundation | SVG/CSS ✅, AbortSignal ✅ (79k+ rounds, zero fires), V8 watch-list + ~40k fuzzer programs + DCHECK-oracle replay ✅ | Blink HTML tokenizer/DOM parser (very heavily fuzzed upstream — low expected value) · Canvas2D raster paths |
| Ad-privacy plumbing | ✅ Protected Audience / DIPS / fenced-frame remnants — the code was largely *removed* at our revision; remnant audit clean | — structurally dead |
| Recon & targeting legs (no memory bug needed) | partially — WebRTC srflx leak documented | cookie-sync graph edges, header-enrichment interplay (Citizen Lab's pending DARK CARTOGRAPHER report will map this) |

**Reading of the map:** everywhere the chain's *earliest* stages touch (bytes → decoders), the legacy C++ has been structurally replaced (wuffs, Rust, Fontations) or audited clean — the "2008-era attack surface" is gone at this revision. What remains unexamined clusters in two places: **codec decode interiors** (ffmpeg/NALU) and **the network/session layer** (WebGL/ANGLE, `//net` parsers, WebTransport, storage). Those are also the cones where Google's own fuzzing is thickest — expect them to be armored, but the map should say so with evidence, not assumption.
