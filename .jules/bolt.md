## 2026-03-08 - Rate Limiter O(N) Anti-Pattern
**Learning:** Using `defaultdict(list)` for sliding window rate limiting creates an O(N) performance bottleneck because filtering expired timestamps requires rebuilding the list on every request.
**Action:** Use `collections.deque` for time-series data where elements are strictly ordered. This allows O(1) removal of old elements using `popleft()` and avoids memory allocation overhead from list comprehensions.

## 2026-03-08 - Rate Limiter O(N) Tuple Allocation
**Learning:** Iterating over `list(dict.items())` for periodic cleanup creates a full copy of the dictionary as tuples, which is O(N) memory and time.
**Action:** Iterate over `list(dict)` (keys only) to avoid tuple creation and allow in-place deletion (`del dict[key]`) within the loop, reducing memory pressure.
