## 2026-05-20 - Rate Limiter Optimization
**Learning:** Periodic cleanup of resources (like rate limiter keys) can cause latency spikes proportional to the number of tracked items (O(N)).
**Action:** Use a continuous, amortized O(1) cleanup strategy. By maintaining a global deque of all request timestamps, we can check only the oldest (expired) requests on each call, eliminating bursty cleanup cycles.
