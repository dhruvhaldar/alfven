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
