# chromium-adware-research

**Where could an ad hurt Chrome?** — an independent, open research notebook about the attack surface that web advertising touches in Chromium, started after the Citizen Lab "AdFection" revelations.

## Why this exists (the 30-second version)

In October 2026, Citizen Lab published [**Exposing AdFection**](https://citizenlab.ca/research/how-discover-tech-turned-targeted-ads-into-a-pipeline-for-spyware/) — the first confirmed case of **zero-click mercenary spyware delivered through targeted ads**. An ad-tech company won ad auctions, and the winning "ad" was actually a delivery vehicle: it served exploit code straight into the browser of the specific person being targeted, and harmless blank bytes to everyone else (so ad-scanners never saw anything).

We asked a simple question: **if an attacker owns the ad slot — if their code runs inside an ordinary cross-origin ad iframe on any page — which parts of Chrome's open-source code could it actually attack?** And the flip side: which parts are armored?

This repo is our honest answer: a small number of findings, a large number of "we checked, it's solid" verdicts, and the method we used to tell them apart.

## Repo map

| Path | What's in it |
|---|---|
| [`docs/WHY-THIS-RESEARCH.md`](docs/WHY-THIS-RESEARCH.md) | The full origin story and the threat model |
| [`docs/DELIVERY-BAR.md`](docs/DELIVERY-BAR.md) | The filter we graded every finding against ("could an ad deliver this?") |
| [`docs/FURTHER-DIRECTIONS.md`](docs/FURTHER-DIRECTIONS.md) | Where to dig next — in Chromium and around it |
| [`poc/abortsignal-adframe/`](poc/abortsignal-adframe/) | Runnable stress engine for the AbortSignal abort-list bug class (upstream-known, crbug 40068730), with an ELI5 |
| [`findings/`](findings/) | Embargoed findings — verified bugs reported to upstream; details publish after they're fixed |
| [`audits/`](audits/) | The negative results: everything we line-by-line audited and found **clean** (this is a feature of the repo, not a failure) |

## Findings status

| Finding | Class | Status |
|---|---|---|
| AbortSignal abort-list stress engine | UAF bug-class hunt (upstream-known crashes, we mapped what *doesn't* trigger them) | Public here — see `poc/` |
| MediaStream device-observer UAF ("M1") | Memory corruption (renderer) — *disproven before filing* | ❌ The "verified chain" was a composition error — the sync-JS branch and the write branch are mutually exclusive by an explicit guard. See [`audits/NEGATIVE-RESULTS.md`](audits/NEGATIVE-RESULTS.md) entry 9 |
| UserScript world messaging toggle failure | Security control silently fails | 🔒 Runtime-proven; reported — details embargoed until fix |
| BMP alpha-mask stale-slot "leak" | Hypothesized info leak | ❌ Refuted by discriminator: the stale value is never the primer's mask (entry 18) |
| ICO/BMP, GIF, PNG, JPEG, WebP, JXL, AVIF, MSE demuxers, WebRTC SCTP, fenced-frame remnants, V8 watch-list, webfont pipeline | — | ✅ Audited clean; see `audits/` |
| Webfont table delegation | Structural observation (public-source-derived) | 📌 Blink passes 20 font tables to HarfBuzz *unsanitized by design* — making HB's layout engine the last big C++ webfont surface. Mapped in [`audits/WEBFONT-PIPELINE.md`](audits/WEBFONT-PIPELINE.md) |

## The honest headline

Chrome's ad-adjacent surface is **armored**, and the armor is now mapped cone by cone. Across this project: line-by-line audits of the *entire* image-decoder family, the MSE media demuxers, and the web-font pipeline; parser-rewrite verification in WebRTC; ~40,000 fuzzer-generated programs replayed; targeted invariant-stress against known-weak V8 patterns — zero memory-safety bugs found in the cones we checked. The most interesting output isn't a clean verdict: it's where the armor *thins*. The image family's 2008-era C++ is simply gone (wuffs/Rust), and web fonts funnel their unsanitized tables into one place — HarfBuzz, the last big C++ parser standing in that path, in the renderer, on every platform. The AdFection-style actors don't find these bugs cheaply either; that's why a working browser exploit chain sells for millions. Our negative results are the evidence, and they're logged as carefully as a find would be.

## Ground rules

1. **Responsible disclosure only.** Nothing that would help weaponize an unpatched bug gets published here; verified findings appear as embargo stubs until upstream fixes them.
2. **Negative results are results.** "We checked X and it's solid" gets the same documentation as a find.
3. **No attribution games.** This is about Chrome's code, not about tracking any specific actor.

## Credits & sources

- Citizen Lab, *Exposing AdFection* (Report 195, Oct 2026) — the origin.
- Confiant, *ADINT weaponized* (Oct 2026) — independent technical companion on the same ad pipeline.
- All Chromium analysis is against public source at a pinned revision (see audit docs for the pin).

*This is independent research. Not affiliated with or endorsed by Google.*
