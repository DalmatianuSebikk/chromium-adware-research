# 🔒 M1 — MediaStream device-observer use-after-free (EMBARGOED)

**Status:** verified chain, reported to Google via Chrome VRP. **Full details, the vulnerable code, and the reproduction recipe will be published here after the report is resolved and a fix ships.**

## What we can say now

- **Class:** memory corruption (use-after-free write) in the Chromium renderer's media-stream bookkeeping.
- **How it was found:** line-by-line source analysis of the device-lifecycle code paths, at a pinned public revision of Chromium.
- **Why it's embargoed:** it is a genuine memory-corruption chain. Publishing before a fix would hand it to exactly the kind of actors this research project exists to study (see [`docs/WHY-THIS-RESEARCH.md`](../../docs/WHY-THIS-RESEARCH.md)).
- **Delivery-bar grade:** fails the bar for the ad-attack scenario (needs a user gesture and a permission prompt to arm) — real bug, wrong shape for the AdFection threat model. That grading is why it's a bounty report rather than a weapon narrative.

## What ships here after the fix

1. ELI5 explanation
2. The vulnerable code with file/line references
3. The full trigger chain (step by step, synchronous-dispatch path included)
4. Why the sibling code path *was* hardened against this exact pattern and this one wasn't — the part reviewers found most compelling

*Timeline expectation: Chrome VRP triage → fix → a release or two → we publish. If you're reading this and the stub is still up, the clock is still running.*
