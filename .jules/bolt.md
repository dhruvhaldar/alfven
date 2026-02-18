## 2026-03-08 - Rate Limiter O(N) Anti-Pattern
**Learning:** Using `defaultdict(list)` for sliding window rate limiting creates an O(N) performance bottleneck because filtering expired timestamps requires rebuilding the list on every request.
**Action:** Use `collections.deque` for time-series data where elements are strictly ordered. This allows O(1) removal of old elements using `popleft()` and avoids memory allocation overhead from list comprehensions.
