## 2025-02-18 - Resource Exhaustion in Simulation Loops
**Vulnerability:** The `IonosphereInput` model allowed unlimited `steps` and `layers`, causing an $O(N \times M)$ loop in `ChapmanProfile.density` that could be exploited for DoS.
**Learning:** Physics simulation inputs often have multiplicative complexity. Simple type checks are insufficient; numerical bounds are critical.
**Prevention:** Always use `le` (less than or equal) constraints in Pydantic fields for loop counters, and validate list lengths.
