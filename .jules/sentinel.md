## 2025-02-18 - Resource Exhaustion in Simulation Loops
**Vulnerability:** The `IonosphereInput` model allowed unlimited `steps` and `layers`, causing an $O(N \times M)$ loop in `ChapmanProfile.density` that could be exploited for DoS.
**Learning:** Physics simulation inputs often have multiplicative complexity. Simple type checks are insufficient; numerical bounds are critical.
**Prevention:** Always use `le` (less than or equal) constraints in Pydantic fields for loop counters, and validate list lengths.

## 2026-02-14 - Polyfill.io Supply Chain Attack
**Vulnerability:** The codebase used `polyfill.io` to load polyfills. This domain was compromised and used to serve malware.
**Learning:** Relying on third-party CDNs without integrity checks (SRI) or using services with ownership changes can introduce critical vulnerabilities.
**Prevention:** Use reputable CDNs (like cdnjs, jsDelivr) and enable Subresource Integrity (SRI) checks where possible. Prefer bundling dependencies or using modern browser features without polyfills.
