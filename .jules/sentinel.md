## 2024-05-23 - Rate Limiter Reset Vulnerability
**Vulnerability:** The rate limiter cleared *all* IP tracking data when the `MAX_IPS` limit was reached. This allowed an attacker to bypass rate limits by flooding the system with spoofed IPs to trigger a global reset.
**Learning:** "Fail-safe" mechanisms (like clearing a cache to prevent OOM) can inadvertently become "fail-open" security vulnerabilities. A security control should degrade gracefully (e.g., LRU eviction) rather than collapsing entirely.
**Prevention:** Use LRU eviction strategies for bounded caches instead of `clear()`. Also, ensure secondary structures (like global logs) are also bounded to prevent memory exhaustion, even if it means sacrificing some precision (fail-secure).
