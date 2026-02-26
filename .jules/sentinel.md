## 2024-05-23 - Rate Limiter Reset Vulnerability
**Vulnerability:** The rate limiter cleared *all* IP tracking data when the `MAX_IPS` limit was reached. This allowed an attacker to bypass rate limits by flooding the system with spoofed IPs to trigger a global reset.
**Learning:** "Fail-safe" mechanisms (like clearing a cache to prevent OOM) can inadvertently become "fail-open" security vulnerabilities. A security control should degrade gracefully (e.g., LRU eviction) rather than collapsing entirely.
**Prevention:** Use LRU eviction strategies for bounded caches instead of `clear()`. Also, ensure secondary structures (like global logs) are also bounded to prevent memory exhaustion, even if it means sacrificing some precision (fail-secure).

## 2024-05-24 - Rate Limit Bypass via Header Spoofing
**Vulnerability:** The application manually parsed `X-Forwarded-For` and trusted it, allowing attackers to bypass rate limits by rotating the header value. This occurred because the app blindly trusted the header without verifying if the request actually came from a trusted proxy.
**Learning:** Application code should not attempt to parse proxy headers manually unless it has a robust configuration for trusted proxies. Blindly trusting headers introduces spoofing risks.
**Prevention:** Rely on the ASGI server (Uvicorn/Gunicorn) to handle proxy headers and populate `request.client.host` securely. Ensure production deployments configure the server with `--proxy-headers` and restricted `--forwarded-allow-ips`.

## 2026-06-01 - JSON Serialization DoS via Infinite Floats
**Vulnerability:** Pydantic's default float validation allows infinite values (e.g., from physics formulas with near-zero denominators), but standard JSON serialization fails on `Infinity`, causing unhandled 500 errors and potential denial of service.
**Learning:** Input validation must account for domain-specific edge cases (like division by zero) and data serialization limits, not just type correctness.
**Prevention:** Enforce strict numerical bounds (e.g., `le=...`, `ge=...`) on all float inputs that feed into calculations, preventing overflow/underflow before processing.
