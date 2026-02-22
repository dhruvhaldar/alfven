## 2026-05-20 - Rate Limiter Optimization
**Learning:** Periodic cleanup of resources (like rate limiter keys) can cause latency spikes proportional to the number of tracked items (O(N)).
**Action:** Use a continuous, amortized O(1) cleanup strategy. By maintaining a global deque of all request timestamps, we can check only the oldest (expired) requests on each call, eliminating bursty cleanup cycles.

## 2026-05-21 - Frontend Visualization Optimization
**Learning:** Recreating SVG elements (clearing innerHTML) on every update causes significant DOM thrashing and layout recalculation, especially during high-frequency events like dragging a slider.
**Action:** Use D3.js's selection/update pattern to reuse existing DOM nodes. Initialize static elements once and only update dynamic attributes (like `d` path data) on subsequent calls.
