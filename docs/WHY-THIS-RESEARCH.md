# Why this research exists

## The event

On October 15, 2026, the Citizen Lab published [**"Exposing AdFection"**](https://citizenlab.ca/research/how-discover-tech-turned-targeted-ads-into-a-pipeline-for-spyware/) (Report 195). It documented, for the first time, a **zero-click spyware pipeline built out of the ordinary machinery of online advertising**:

- An Israeli company (Discover-Tech) operated both a legitimate-seeming DSP (demand-side platform — the software that bids on ads) and a mercenary surveillance platform.
- When it won an ad auction, the "creative" (the ad content) it delivered was a **loader**: a small script that fetched code from attacker servers.
- Those servers decided **per viewer** — using the IP address baked into every ad request — whether to serve the real payload or empty bytes. Only the intended victim ever received the attack; every scanner, researcher, or monitoring system saw nothing.
- The payload stage was never captured, but the end result was commercial spyware on journalists' devices.

Confiant's companion research ([*ADINT weaponized*](https://blog.confiant.com/p/adint-weaponized-ad-tech)) independently mapped the same infrastructure: a ~90 KB obfuscated SDK inside a 1×1 iframe, fingerprinting probes, encrypted command channels (including WebRTC as a transport), and arbitrary code pushed through `new Function(...)` — all running **with the authority of an ad frame on a normal publisher page**.

## The question we asked

Everything above the exploit is well documented. The exploit itself — the part that turns "attacker JS in an ad frame" into "code running outside the sandbox" — was never seen. So we asked:

> **If your only foothold is an ordinary cross-origin ad iframe on someone's page — no click, no permission prompt, no extension, no compromise of the publisher — what in Chromium's public source code can you actually attack?**

That's a source-code research question. Chromium is open; the answer has to be in there.

## What made it interesting

1. **The ad frame is the perfect attacker.** Its contents are attacker-chosen bytes on attacker-chosen timing, embedded in pages the victim simply visits. Zero-click by construction.
2. **Chrome's response to AdFection was ecosystem severance, not a code fix.** No CVE was ever disclosed for the exploit stage. Whatever bug class it used is, as far as anyone publicly knows, either still present or was quietly patched without credit.
3. **A huge fraction of the attack surface is under-examined**, because ad delivery touches unusual corners: image decoders fed multipart re-feeds, WebRTC, timer and scheduling APIs, storage partitioning, the tattered remnants of the Privacy Sandbox.

## What we actually did

- Mapped Chromium's ad-delivery path (fenced frames, Protected Audience remnants, DIPS, sniffing, multipart image re-feeds) and graded every candidate bug against the **delivery bar** (see [DELIVERY-BAR.md](DELIVERY-BAR.md)).
- Line-by-line audited the legacy image decoders (ICO/BMP), the SCTP/WebRTC parser surface, and several V8 invariant patterns — all clean; the audits are in [`audits/`](../audits/).
- Built a runnable stress engine against the one upstream-known bug class that *is* ad-deliverable (AbortSignal abort-list crashes, crbug 40068730) — see [`poc/abortsignal-adframe/`](../poc/abortsignal-adframe/).
- Verified one memory-corruption chain and one security-control failure, both **reported to upstream and embargoed** until fixed — see [`findings/`](../findings/).
- Ran coverage-guided fuzzing (~40k programs) and replayed an 18k-program corpus against a DCHECK-enabled build — zero violations.

## The honest conclusion

The cones we could reach are armored. We do not read that as "we failed" — we read it as the measured difficulty of the thing AdFection actors actually did, which is consistent with what the exploit market pays for this class of bug. The map of what-is-solid is itself the deliverable, and the remaining un-audited surface is listed in [FURTHER-DIRECTIONS.md](FURTHER-DIRECTIONS.md) for whoever digs next — maybe us, maybe you.
