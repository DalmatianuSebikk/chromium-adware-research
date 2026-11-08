# Negative results registry

*Everything we checked and found solid. Each entry cost real work; each "clean" is a fact about where Chrome's armor actually is. Repeating any of these would waste someone's time — so they're written down.*

| # | What was checked | How | Verdict |
|---|---|---|---|
| 1 | **ICO/BMP legacy decoders** | line-by-line source audit (full detail: [`IMAGE-DECODERS.md`](IMAGE-DECODERS.md)) | ✅ Clean (2 DoS-class soft spots, no memory bug) |
| 2 | **WebRTC SCTP/ICE parser surface** | source audit of parser rewrite + legacy shapes | ✅ Clean (the CVE-2022-2294 shape is structurally eliminated by the span-based rewrite) |
| 3 | **Fenced-frame / Protected Audience remnants** | dangerous-function pass over the wind-down scaffolding | ✅ Clean (hardening notes only; the ad-privacy code was largely *removed*, not just disabled) |
| 4 | **V8 watch-list invariants** (typer/deopt/media/range classes) | targeted stress programs against a `dcheck_always_on` + slow-DCHECK build | ✅ Clean — none of the latent patterns fire without compiler-internal shapes |
| 5 | **18,341-program corpus replay** on DCHECK build | full replay with timeout + classification harness | ✅ Zero violations, zero crashes |
| 6 | **~40,000 fuzzer-generated programs** (coverage-guided, V8 profile) | two long-running campaigns + watchman | ✅ Zero crashes |
| 7 | **AbortSignal abort-list chaos** (upstream-known bug class, crbug 40068730) | the engine in [`poc/abortsignal-adframe/`](../poc/abortsignal-adframe/) — 79k+ rounds, 38M fetches, 90M in-loop allocations, all five re-entry modes | ✅ Zero fires — weak-set iteration is defended against plain mid-loop mutation |
| 8 | **Ubsan runtime** on the DCHECK build | halt-on-error replay | ✅ No undefined behavior reports |

## What the negatives add up to

- Chrome's ad-reachable decoding and media paths are **fuzzed and audited to a level** that a solo effort with targeted methods doesn't crack by breadth.
- The DCHECK-oracle method (entries 4–5) works — it just needs **pointed inputs**, not random ones: every invariant we probed needed a compiler-pipeline-specific shape to have any chance.
- Entry 7 is the most instructive: an upstream-tracked crash class, a fully ad-deliverable surface, an engine that does everything the crashes imply — and the release instrumentation never fires. The armor below the surface is real.

## Reproducing any entry

- Entries 4–5: build V8 with `is_debug=false dcheck_always_on=true v8_enable_slow_dchecks=true`, replay any corpus with the flags listed in the stress scripts.
- Entry 6: Fuzzilli with the V8 profile, `--storagePath` corpus, jobs scaled to the machine.
- Entry 7: run the PoC (see its ELI5) and watch the renderer console.
