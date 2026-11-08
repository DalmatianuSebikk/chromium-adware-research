# The delivery bar

*How we decided which bugs matter for the ad-attack story — explained simply.*

## The idea

Not every real Chrome bug can be used by an ad. A memory-corruption bug that only triggers when the user clicks "Allow" on a screen-capture prompt is a *real* bug — Google will pay for it — but it is **not an AdFection-shaped weapon**, because the attacker in the ad scenario doesn't get a click or a prompt. The victim just loads a page with an ad slot.

So every candidate finding got graded against one question:

> **Can this be triggered by an ordinary cross-origin ad iframe — no click, no permission prompt, no extension, no control over the publisher page?**

Pass = worth building a weapon narrative around. Fail = still reportable, but not this threat model.

## The three grades

1. **PASSES the bar** — plain page JS in a cross-origin iframe can reach the buggy code. Example: an AbortSignal bug reachable from `fetch().abort()` — an ad does fetches constantly, and nobody grants permissions for that.
2. **Fails the bar** — needs a user gesture, a permission prompt, browser-UI mediation, or an extension/browser-level actor. Real bug, wrong shape.
3. **Recon-class** — doesn't corrupt memory but leaks information (IP addresses, identifiers) that the *targeting* stage of an ad attack needs. Lower severity, perfectly on-theme: AdFection's targeting needed exactly this.

## The one multiplier

**Android WebView.** Most mobile in-app ads render in a WebView, and WebView is structurally softer than Chrome-the-browser: historically no site isolation between iframes inside it, and one renderer process for the whole embedded browser. A bug that's merely a renderer crash in desktop Chrome can be a renderer-compromise-adjacent event inside an app on Android. Every renderer finding gets "+1 severity" in the WebView world. (76.7% of the AdFection campaign's impressions were in-app.)

## Worked example

**Grading a real finding with the bar:**

- *AbortSignal abort-list crashes* → the triggering API (`fetch` + `AbortController`, `AbortSignal.timeout()`, `Observable.subscribe(..., {signal})`) is all plain page JS, no prompts → **PASSES**. An ad can run the entire engine.
- *The MediaStream device-observer chain* (see `findings/`) → beautiful verified chain, but entry needs a capture permission prompt and picker interaction → **fails the bar** → reported to Google, kept out of the weapon narrative.
- *WebRTC srflx candidate leak* → no memory corruption, but reveals the real client IP behind proxies with zero permissions → **recon-class PASS** (this is literally one of AdFection's targeting legs).

## Why "explain like I'm 5" is load-bearing

Part of this project's goal is that a non-expert — an editor, a policy person, a journalist, a curious developer — can follow *why* an ad-platform spyware pipeline is a browser-engine problem. Every PoC and audit in this repo therefore carries an ELI5 next to the technical version. If the simple version is wrong, the technical version doesn't save it.
