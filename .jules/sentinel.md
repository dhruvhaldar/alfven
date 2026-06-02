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

## 2026-03-01 - [Information Leakage & XSS Risk via Pydantic Validation Errors]
**Vulnerability:** When a `RequestValidationError` occurred, the global exception handler directly serialized the raw `exc.errors()` via `jsonable_encoder` and returned it in the HTTP 422 response.
**Learning:** In Pydantic v2, `exc.errors()` automatically includes the original rejected input under the `input` key, and a documentation `url` key. If an attacker provides malicious payloads (e.g., extremely large strings or potential XSS vectors), reflecting it back verbatim exposes the application to log injection, response bloat, and potential client-side reflection issues if the frontend mishandles the error detail.
**Prevention:** Always explicitly sanitize Pydantic `exc.errors()` in custom `RequestValidationError` handlers by stripping the `input` and `url` keys from each error dictionary before serialization.

## 2026-03-01 - Missing Security Headers on Static Assets in Vercel
**Vulnerability:** Security headers (like CSP, HSTS, X-Frame-Options) were only applied in the FastAPI middleware, meaning they were only sent on API responses. In production, Vercel serves the static frontend assets directly, bypassing the backend and leaving the frontend vulnerable to XSS and Clickjacking.
**Learning:** Middleware in serverless backend functions only protects the endpoints it serves. It does not apply to static assets served by the hosting platform's CDN.
**Prevention:** Always duplicate or configure global security headers in the hosting platform's configuration file (e.g., `vercel.json`) to ensure they apply to all routes, especially static HTML files.

## 2026-11-13 - [Missing Audit Logging for Rate Limit Events]
**Vulnerability:** The rate limiter successfully blocked requests exceeding the permitted threshold but failed to log these events.
**Learning:** Silently dropping or rejecting requests without logging leaves the application blind to ongoing DoS attacks, brute-force attempts, or abusive client behavior.
**Prevention:** Always add explicit audit logging (e.g., `logger.warning`) when enforcing security boundaries like rate limits, including identifying information like the client IP and the requested path.

## 2026-11-20 - [Memory Exhaustion DoS via Unbounded Header Storage]
**Vulnerability:** The rate limiter extracted the client IP from the `X-Forwarded-For` header and used it directly as a dictionary key (`request_counts`). An attacker could provide a massive, unbounded string in this header (e.g., 1MB long), which would be allocated in memory. Since `MAX_IPS` allowed up to 2000 unique keys, this could exhaust gigabytes of memory and crash the server.
**Learning:** Limiting the number of keys in a dictionary (e.g., LRU cache) prevents unbounded item growth, but it does not protect against unbounded memory growth if the size of the individual keys (or values) is not restricted.
**Prevention:** Always enforce a strict maximum length (e.g., 45 characters for IPv6) when extracting string values from untrusted HTTP headers before storing them in memory or passing them to backend components.

## 2026-03-01 - [Memory Exhaustion DoS via Missing Content-Length in Body Limits]
**Vulnerability:** The API middleware intended to enforce a maximum request body size (100KB) only checked the `Content-Length` header if it was present. By omitting this header on a `POST` request (while not using chunked encoding), an attacker could bypass the middleware check. FastAPI would then attempt to read the entire unbounded body into memory, potentially leading to a Memory Exhaustion DoS.
**Learning:** Checking an optional HTTP header like `Content-Length` for a size limit is ineffective if the logic fails to handle requests where the header is deliberately omitted. Defense-in-depth requires failing closed when critical validation information is missing.
**Prevention:** Always explicitly require the `Content-Length` header (e.g., returning a `411 Length Required` response) on `POST`, `PUT`, and `PATCH` requests when enforcing maximum upload sizes, ensuring body length is bounded before any processing occurs.

## 2026-11-20 - [Log Injection Vulnerability via Unsanitized Request Path]
**Vulnerability:** The rate limit middleware logged the requested path (`request.scope.get("path")`) when a limit was exceeded. Because URL paths are typically URL-decoded by ASGI servers, an attacker could supply a path containing `%0A` (newline) or `%0D` (carriage return). When logged verbatim by `logger.warning`, this allowed the attacker to inject arbitrary, fake log entries on new lines (Log Forging / Log Injection).
**Learning:** Any data originating from the HTTP request (including paths, headers, and query parameters) is inherently untrusted. Standard Python logging functions do not automatically escape newlines within the message string, allowing log structure to be manipulated if inputs aren't sanitized.
**Prevention:** To prevent Log Injection / Log Forging vulnerabilities, always explicitly sanitize untrusted request data by escaping control characters (e.g., `path.replace("\n", "\\n").replace("\r", "\\r")`) before passing it to the application logger.

## 2025-05-18 - Middleware Short-Circuit Security Header Bypass
**Vulnerability:** Security headers were missing on early-return error responses (429, 413, 411) from rate limiting and upload size middlewares.
**Learning:** In FastAPI, middleware is executed in reverse order. If an outer middleware returns a response directly, it bypasses inner middlewares, including the one responsible for applying security headers.
**Prevention:** Apply security headers directly to early-return responses in middleware or use a custom Exception to leverage centralized exception handlers instead of returning responses directly.
