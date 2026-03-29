## 2026-03-01 - [Rate Limit Bypass via X-Forwarded-For Spoofing]
**Vulnerability:** The Vercel reverse proxy IP extractor parsed the left-most (`[0]`) IP address from the `X-Forwarded-For` chain. This allows an attacker to inject spoofed IPs in the request header, which Vercel appends to, bypassing the IP-based rate limiter since the backend incorrectly trusted the client-supplied IP instead of the proxy-supplied connection IP.
**Learning:** Standard reverse proxies typically append the real connection IP to any existing `X-Forwarded-For` header. Thus, when sitting behind a single trusted proxy (like Vercel), the true client IP is the right-most address (`[-1]`).
**Prevention:** Always extract the right-most IP address (`split(",")[-1]`) from the `X-Forwarded-For` header when processing requests behind a single layer reverse proxy, or rely on trusted platform-specific headers like `x-real-ip` or `x-vercel-forwarded-for`.

## 2026-03-01 - [DOM-based XSS via innerHTML assignments]
**Vulnerability:** Several frontend JavaScript files were using `element.innerHTML = '...'` to insert dynamic error messages or data into the DOM. This introduces a risk for DOM-based Cross-Site Scripting (XSS) if the input data or message ever originates from unvalidated user input or untrusted APIs.
**Learning:** Even if the input seems safe or is purely numerical/hardcoded at the moment, relying on `innerHTML` for displaying simple text or values builds a vulnerable pattern that can be accidentally exploited in the future when the data source changes.
**Prevention:** Always enforce the use of `element.textContent = '...'` for dynamic text assignment. For styling previously applied inline through injected HTML tags, configure the element's style directly via `element.style` or toggle CSS classes instead.
## 2026-03-01 - Missing Subresource Integrity (SRI) for External Dependencies
**Vulnerability:** External scripts (e.g., Three.js, D3.js, Chart.js, MathJax, polyfill) were loaded from CDNs without `integrity` and `crossorigin="anonymous"` attributes.
**Learning:** Loading scripts directly from CDNs without validating their integrity allows for a supply chain attack. If a CDN is compromised, malicious code could be injected and executed on the client-side, bypassing existing Content Security Policy (CSP) protections since the CDN domains were whitelisted.
**Prevention:** Always generate and include SHA-384 cryptographic hashes via the `integrity` attribute and set `crossorigin="anonymous"` when loading third-party scripts or stylesheets from external CDNs.

## 2026-03-01 - [Information Exposure via API Response Caching]
**Vulnerability:** API endpoints returning potentially sensitive or dynamic calculations did not explicitly set `Cache-Control` headers. This could allow intermediate proxies, CDNs, or browser caches to store and expose these responses.
**Learning:** By default, if cache headers are omitted, intermediate nodes might heuristically cache GET request responses, potentially leading to stale data or information leakage.
**Prevention:** Always enforce strict `Cache-Control: no-store, no-cache, must-revalidate, max-age=0` headers for all dynamic API endpoints to ensure data is never inadvertently cached.

## 2026-10-30 - Missing Security Headers on 500 Error Responses
**Vulnerability:** Unhandled exceptions resulting in 500 Internal Server Error responses bypassed the custom `add_security_headers` HTTP middleware in FastAPI/Starlette, causing these error pages to lack critical security headers like Content-Security-Policy (CSP) and Strict-Transport-Security (HSTS).
**Learning:** In the Starlette/FastAPI request lifecycle, custom exception handlers defined via `@app.exception_handler(Exception)` intercept unhandled exceptions and return a response directly. While the `http` middleware still wraps this flow, if an exception is raised *within* `call_next(request)` (as happens before it is caught by the exception handler), the middleware execution is aborted. Thus, code placed after `call_next(request)` in the middleware does not execute for these errors.
**Prevention:** Extract security header addition logic into a standalone helper function. Apply this function both within the custom middleware (for successful/handled requests) and explicitly within the custom global exception handler to ensure comprehensive coverage across all response types.

## 2026-03-01 - [Missing Security Headers on 4xx Error Responses]
**Vulnerability:** Framework-generated error responses such as 422 Unprocessable Entity (from `RequestValidationError`) and 404 Not Found (from `StarletteHTTPException`) bypassed the custom `add_security_headers` HTTP middleware in FastAPI/Starlette, causing these error pages to lack critical security headers like Content-Security-Policy (CSP) and Strict-Transport-Security (HSTS).
**Learning:** In the Starlette/FastAPI request lifecycle, handled exceptions like validation errors and 404s bypass normal middleware if they are intercepted by their specific built-in exception handlers before the middleware pipeline completes.
**Prevention:** Define explicit exception handlers for `RequestValidationError` and `StarletteHTTPException`. Within these handlers, explicitly apply the shared security header logic before returning the response. Also ensure `exc.headers` are properly passed when overriding `StarletteHTTPException` to preserve critical protocol headers (like `WWW-Authenticate`), and use `fastapi.encoders.jsonable_encoder` to safely serialize validation error context.
## 2026-11-06 - Missing Retry-After Header in Rate Limiter
**Vulnerability:** The `rate_limit_middleware` returned a `429 Too Many Requests` response without a `Retry-After` header. While it successfully blocked requests, it left well-behaved clients guessing when to retry, potentially leading to accidental self-inflicted Denial of Service (DoS) as clients continuously poll.
**Learning:** Returning a `429` status code is only half of rate limiting. Without a defined back-off period, automated clients cannot efficiently manage their request rates.
**Prevention:** For API rate-limiting logic, always calculate and include a `Retry-After` header in seconds to instruct clients when to retry.
