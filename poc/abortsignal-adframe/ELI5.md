# AbortSignal abort-list stress engine — ELI5 + technical brief

## What this is

A runnable web page pair (a "publisher" page and a cross-origin "ad" page, exactly like a real ad slot) that hammers a known-fragile part of Chrome: the code that runs when you cancel downloads. It has been running for tens of thousands of automated rounds with **zero crashes** — and that negative result is the point (see below).

## ELI5 — explain like I'm 5

When a web page starts a download, it can attach a little note saying *"if I ever shout STOP, cancel this download."* Chrome keeps all these STOP-notes on a **list**.

Here's the tricky part: when you shout STOP, Chrome walks down the list and cancels everything, **and the things being cancelled are allowed to run web-page code right then, in the middle of the walk** — code that can add things to the list, take things off, or make other lists fire too.

That's like being allowed to rearrange a marching band's line *while the band is marching* — if you do it wrong, someone marches into empty space. Real Chrome has crashed this way in the wild (Google's own bug tracker has the crashes, and Chrome engineers added alarm-bells — `CHECK`s — to the code to learn more about them).

Our page is a **band-rearranging machine**: it creates thousands of downloads, cancels them, adds and removes STOP-notes mid-cancellation, triggers timeouts, destroys worker pages mid-shout — millions of times, in every combination we could think of, **from inside a plain ad iframe, with no clicks and no permissions**.

Result so far: **Chrome held.** No crashes, no alarm-bells. The marching band survives our chaos. That tells Google's engineers (and us) that the wild crashes need a rarer trick than plain list-rearranging — and tells the rest of us this particular door is *more* locked than the bug reports make it look.

## The technical brief

**Bug class:** use-after-free candidate in `AbortSignal::RunAbortSteps` — iteration over `abort_algorithms_` (a `HeapLinkedHashSet<WeakMember<AlgorithmHandle>>`) while the executed algorithms can synchronously re-enter JS and mutate the set. Upstream knows wild crashes exist (Chromium issue 40068730) and ships release-mode `CHECK(handle)` instrumentation plus `SCOPED_CRASH_KEY_NUMBER("AbortSignal", "size_before"/"current_size")` crash keys as diagnostic canaries — present in current Canary builds.

**The vulnerable code** (`third_party/blink/renderer/core/dom/abort_signal.cc`, at our pinned revision):

```cpp
void AbortSignal::RunAbortSteps() {
  ...
  // Pass 1: CHECK-only loop over weak handles
  for (AlgorithmHandle* handle : abort_algorithms_) {
    CHECK(handle);  // upstream diagnostic canary
  }
  // Pass 2: run the algorithms — each Run() may execute
  // SYNCHRONOUS PAGE JS (fetch abort, Observable teardown, ...)
  // which can mutate abort_algorithms_ (weak handles dying,
  // nested aborts via AbortSignal.any composition, ...)
  for (AlgorithmHandle* handle : abort_algorithms_) {
    SCOPED_CRASH_KEY_NUMBER("AbortSignal", "current_size", ...);
    CHECK(handle);
    CHECK(handle->GetAlgorithm());
    handle->GetAlgorithm()->Run();   // <-- re-entry point
  }
  ...
}
```

Why it's interesting to stress: handles are held **weakly** — a garbage-collection pause between iterations can unlink the next node; `fetch` loaders register abort algorithms but never unregister them (accumulating dead weak handles); and `Observable.subscribe(observer, {signal})` teardown runs **user JS synchronously inside the loop**, including code that can abort other signals.

**What the engine does** (5 rotating modes, all from the cross-origin ad iframe):

| Mode | Shape |
|---|---|
| `sub` | Observable subscriptions whose teardowns allocate heavily and 50% of the time abort a nested controller mid-run |
| `detach` | same-origin child iframe armed with fetches on the parent's signal; remove-vs-abort orderings shuffled |
| `worker` | dedicated workers abort-storming internally, terminated eagerly at random 30–400 ms lifetimes |
| `timeout` | `AbortSignal.timeout()` fleets composed via `AbortSignal.any()` into fetch fleets |
| `base` | direct fetch/scheduler/any-chain load with GC pressure before each abort |

**Scale so far:** tens of thousands of rounds; 38M+ fetches; 90M+ in-loop allocations; ~690k timeout-settles. **Zero `CHECK` fires, zero crashes.**

**Interpretation (honest):** Oilpan's weak-set iteration is structurally defended against plain mid-loop GC unlink — a suspended iterator is conservatively traced, and unlinking patches the next pointers. The wild crashes therefore need something rarer: eager destruction of *other* handles mid-loop (e.g. via `AbortSignal.any` composition), cross-thread/context teardown racing the guard state, or a mechanism entirely different from set mutation. We shared this negative result and the structural analysis upstream.

## How to run it

```sh
cd origin-a-wherever-you-put-it
python3 server.py        # serves publisher on :8801, ad on :8802
# then open http://localhost:8801/publisher.html in Chrome/Canary
# telemetry prints to the console (grep "DOMF1v3"), crashes land in
# chrome://crashes or ~/Library/Logs/DiagnosticReports (macOS)
```

Watch for `Check failed: handle` in the renderer output — that's the upstream alarm-bell firing, i.e. the bug class showing itself. In ~79k rounds we've never seen it.

## Files

- `server.py` — tiny two-origin server (the cross-origin split is the point: it simulates publisher-vs-ad)
- `origin-a/publisher.html` — the "publisher" page; embeds the ad iframe
- `origin-b/ad.html` — the engine (current); `ad-v1.html` (earlier fetch-fleet engine) and `test-obs.html` (single-probe page) included for reference

*Pinned revision and audit context: see [`audits/NEGATIVE-RESULTS.md`](../../audits/NEGATIVE-RESULTS.md). This is a stress tool for a bug upstream already tracks — not an exploit.*
