## 2025-02-18 - Resource Exhaustion in Simulation Loops
**Vulnerability:** The `IonosphereInput` model allowed unlimited `steps` and `layers`, causing an $O(N \times M)$ loop in `ChapmanProfile.density` that could be exploited for DoS.
**Learning:** Physics simulation inputs often have multiplicative complexity. Simple type checks are insufficient; numerical bounds are critical.
**Prevention:** Always use `le` (less than or equal) constraints in Pydantic fields for loop counters, and validate list lengths.

## 2026-02-14 - Polyfill.io Supply Chain Attack
**Vulnerability:** The codebase used `polyfill.io` to load polyfills. This domain was compromised and used to serve malware.
**Learning:** Relying on third-party CDNs without integrity checks (SRI) or using services with ownership changes can introduce critical vulnerabilities.
**Prevention:** Use reputable CDNs (like cdnjs, jsDelivr) and enable Subresource Integrity (SRI) checks where possible. Prefer bundling dependencies or using modern browser features without polyfills.

## 2026-02-18 - In-Memory Rate Limiting Limitations
**Vulnerability:** Simple in-memory rate limiting using `client.host` is vulnerable to IP spoofing (if not behind a proxy) or blocking the load balancer (if behind a proxy). It also leaks memory over time if old IPs are not cleaned up.
**Learning:** While quick to implement, in-memory rate limiting is insufficient for production at scale. It requires external state (Redis) and trusted proxy configuration (`X-Forwarded-For`).
**Prevention:** Use a dedicated rate limiting library (like `slowapi`) backed by Redis and configure trusted proxies explicitly.

## 2026-02-19 - Silent Failure in Global Exception Handling
**Vulnerability:** The global exception handler correctly sanitized 500 error responses to prevent stack trace leakage but failed to log the original exception internally.
**Learning:** Security by obscurity (hiding errors) must be paired with observability (logging errors). A silent failure prevents administrators from detecting and analyzing attack attempts or application bugs.
**Prevention:** Always ensure that exception handlers log the full traceback (`logger.error(..., exc_info=True)`) before returning a sanitized response to the client.
## 2025-02-18 - IP Spoofing in Rate Limiter
**Vulnerability:** The application was using the *first* IP in the 'X-Forwarded-For' header for rate limiting, allowing attackers to bypass limits by spoofing the header (e.g., 'X-Forwarded-For: fake_ip, real_ip').
**Learning:** Prioritizing the first IP is insecure when trusted proxies append the client IP to the end of the list. The first IP is user-controlled and easily forged.
**Prevention:** Always use the *last* untrusted IP (or the last IP if behind a single trusted proxy like a load balancer) in the 'X-Forwarded-For' list. Use 'forwarded.split(",")[-1].strip()' instead of '[0]'.

## 2026-02-19 - DoS via Rate Limiter Reset ("Fail Open")
**Vulnerability:** The in-memory rate limiter cleared its entire state when the IP tracking limit (`MAX_IPS`) was reached to prevent OOM. Attackers could exploit this by flooding the system with distinct spoofed IPs to trigger a reset, effectively bypassing rate limits for themselves.
**Learning:** Security controls that "fail open" (disable themselves) under load become attack vectors.
**Prevention:** Implement LRU (Least Recently Used) eviction policies instead of clearing caches entirely. Drop the least active users to preserve protection for current threats.
