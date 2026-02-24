## 2026-05-20 - Rate Limiter Optimization
**Learning:** Periodic cleanup of resources (like rate limiter keys) can cause latency spikes proportional to the number of tracked items (O(N)).
**Action:** Use a continuous, amortized O(1) cleanup strategy. By maintaining a global deque of all request timestamps, we can check only the oldest (expired) requests on each call, eliminating bursty cleanup cycles.

## 2026-05-21 - Rate Limiter LRU Eviction
**Learning:** Evicting the Least Recently Used (LRU) item from a dictionary using `min(d, key=...)` is an O(N) operation, which can become a bottleneck under high load or DoS attacks.
**Action:** Leverage Python 3.7+ insertion-ordered dictionaries. By popping and re-inserting a key upon access, it moves to the end (Most Recently Used). The first key (`next(iter(d))`) then becomes the LRU item, allowing for O(1) eviction.

## 2026-05-22 - Token Bucket Rate Limiting
**Learning:** Storing timestamps for every request (Sliding Window Log) consumes O(N) memory per user and complicates global cleanup, potentially leading to OOM or redundant storage.
**Action:** Use Token Bucket algorithm. It requires only O(1) space (tokens + last_update) per user and strict O(1) time complexity, eliminating the need for a global request log while maintaining rate limits.
