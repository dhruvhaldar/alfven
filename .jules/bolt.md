## 2025-05-24 - [O(N^2) Layer Construction]
**Learning:** Found an O(N^2) anti-pattern in `get_ionosphere_profile` where `ChapmanProfile` objects were repeatedly recreated in a loop using `__add__` (which copies lists). This scaled quadratically with the number of layers.
**Action:** Always prefer constructing lists first and passing them to the constructor once (O(N)) rather than appending/adding in a loop, especially for stateless physics objects.

## 2025-05-24 - [Parallelize Independent Async Operations]
**Learning:** Found sequential `await fetch` calls in `calcPlasma` where requests were independent. This unnecessarily added latency (T1 + T2).
**Action:** Use `Promise.all([fetch1, fetch2])` to run independent async operations in parallel, reducing total latency to `max(T1, T2)`. This is a low-risk, high-reward pattern for frontend performance.

## 2025-05-24 - [Debounce High-Frequency Inputs]
**Learning:** Found that `oninput` handlers triggering API calls directly (e.g. `calcSunspot`) cause a flood of requests, degrading performance. Separating immediate visual updates from debounced network requests maintains responsiveness while reducing server load.
**Action:** Always debounce event handlers that trigger network requests on rapid input events (like sliders or text inputs), but ensure local UI updates remain immediate.
