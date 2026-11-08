# 🔒 E1 — UserScript world messaging toggle fails silently (EMBARGOED)

**Status:** runtime-proven with a full experiment matrix, reported upstream. **Details and the PoC extension publish here after resolution.**

## What we can say now

- **Class:** a security-relevant control that silently fails — an extension API switch that is supposed to cut user-script worlds off from extension messaging, but doesn't, for worlds that already exist in the current document.
- **Proof strength:** runtime-verified (controlled same-document experiments on a stock Chromium build, code verified byte-identical at the public release tag), not just code reading.
- **Why it's embargoed:** unreported at time of writing; publishing first would burn the disclosure and teach the wrong people.
- **Delivery-bar grade:** extension-adjacent rather than ad-deliverable — included in this repo because it was found by the same method, and "a security toggle that silently fails" is a pattern worth having on the record.

## What ships here after the fix

1. ELI5 explanation
2. The runtime experiment matrix (all four sequences, including the one that exposes the bug)
3. The root cause in the source with file/line references
4. The complete runnable PoC (MV3 extension + probe page)
