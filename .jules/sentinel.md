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

## 2026-03-01 - [Denial of Service & Header Leakage via KeyError in Exception Handlers]
**Vulnerability:** The custom global exception handler and other HTTP error handlers directly accessed `request.scope["path"]` to determine if a request was an API call. If a malformed request or unexpected ASGI scope was processed (e.g., missing the "path" key), this line would throw a `KeyError`, crashing the exception handler itself and returning a raw 500 error that bypassed the `add_security_headers` middleware and leaked information.
**Learning:** In ASGI middleware and exception handlers, you cannot strictly guarantee the presence of every dictionary key in `request.scope`, particularly during edge cases or internal routing errors. Crashing within an exception handler breaks the fallback defense-in-depth safety nets.
**Prevention:** In ASGI exception handlers and middlewares, always use `request.scope.get('path', '')` instead of direct dictionary access like `request.scope['path']`.

## 2026-11-20 - [Log Injection Vulnerability via Unsanitized Client IP]
**Vulnerability:** The rate limit middleware logged the extracted client IP (`client_ip`) when a limit was exceeded. Because client IPs can be derived from untrusted headers like `X-Forwarded-For` (or platform-specific ones like `x-vercel-forwarded-for`), an attacker could supply a string containing `%0A` (newline) or `%0D` (carriage return) in the header. When logged verbatim by `logger.warning`, this allowed the attacker to inject arbitrary, fake log entries on new lines (Log Forging / Log Injection).
**Learning:** Any data originating from the HTTP request, even indirect fields like client IPs derived from headers, is inherently untrusted.
**Prevention:** To prevent Log Injection / Log Forging vulnerabilities, always explicitly sanitize untrusted request data like client IP by escaping control characters (e.g., `client_ip.replace("\n", "\\n").replace("\r", "\\r")`) before passing it to the application logger.

## 2026-11-20 - [Log Injection Vulnerability Bypass via Double-Encoded Path/IP]
**Vulnerability:** The rate limit middleware sanitized `\n` and `\r` from `path` and `client_ip` before logging them using `logger.warning`. However, URL paths and some headers can be URL encoded. If an attacker supplied an encoded newline (e.g. `%0a` or double-encoded like `%250a`), the `.replace("\n", "\\n")` logic would not detect the raw control character, and the payload could be logged verbatim or later unencoded by downstream log ingestion systems, leading to a delayed log injection vulnerability.
**Learning:** Checking for control characters directly is insufficient if the data represents an encoded payload (like a URL or header). The data must first be decoded to its base representation before applying sanitization rules to be effective against evasion techniques.
**Prevention:** Always use `urllib.parse.unquote` to decode variables like `path` and `client_ip` before applying control character replacements (`\n`, `\r`) to prevent encoded-character bypass attacks.

## 2026-11-20 - Transfer-Encoding Chunked Bypass via HTTP Directive Lists
**Vulnerability:** The API middleware intended to block `Transfer-Encoding: chunked` requests to prevent streaming memory exhaustion DoS attacks. However, it performed an exact string match (`request.headers.get("transfer-encoding", "").lower() == "chunked"`). Because the `Transfer-Encoding` header allows a comma-separated list of directives (e.g., `chunked, gzip`), an attacker could send multiple directives to bypass the strict equality check while still leveraging chunked encoding.
**Learning:** Checking for single malicious values using exact equality `==` is fragile when the underlying HTTP specification permits list-based values for that header.
**Prevention:** Always use a substring check (e.g., `"chunked" in transfer_encoding.lower()`) or explicitly parse the comma-separated list when evaluating HTTP headers that support multiple directives (like `Transfer-Encoding`, `Cache-Control`, `Accept`, etc.) to prevent trivial bypasses.

## 2026-11-20 - Transfer-Encoding Chunked Bypass via Duplicate Headers
**Vulnerability:** The `limit_upload_size` middleware extracted the `Transfer-Encoding` header by iterating through `request.scope.get("headers", [])`. However, it used direct assignment (`transfer_encoding = v`), meaning if an attacker provided multiple `Transfer-Encoding` headers (e.g., `chunked` followed by `gzip`), the middleware only validated the last one (`gzip`), completely bypassing the chunked restriction and enabling a Memory Exhaustion DoS via streaming.
**Learning:** HTTP allows multiple headers with the same name. Iterating through a list of header tuples and overwriting a variable on match is a critical vulnerability pattern when dealing with security checks, as it allows attackers to hide malicious payloads in earlier headers.
**Prevention:** When extracting headers from an ASGI scope loop for security validation, always concatenate multiple values for the same key using a comma separator (e.g., `transfer_encoding += b"," + v`) to ensure all directives are evaluated.
## 2026-11-20 - [IP Spoofing Vulnerability via Duplicate X-Forwarded-For Headers]
**Vulnerability:** The `get_client_ip` function extracted the `X-Forwarded-For` header by iterating through `request.scope.get("headers", [])`. However, it used direct assignment (`forwarded = v`), meaning if an attacker provided multiple `X-Forwarded-For` headers, the function only evaluated the last one, completely bypassing IP-based rate limiting and allowing spoofing.
**Learning:** HTTP allows multiple headers with the same name. Iterating through a list of header tuples and overwriting a variable on match is a critical vulnerability pattern when dealing with security checks, as it allows attackers to hide malicious payloads or spoof data in earlier or later headers.
**Prevention:** When extracting headers from an ASGI scope loop for security validation, always concatenate multiple values for the same key using a comma separator (e.g., `forwarded += b"," + v`) to ensure all directives and IPs are evaluated.
## 2026-11-20 - [Memory Exhaustion DoS Bypass via Duplicate Content-Length Headers]
**Vulnerability:** The `limit_upload_size` middleware extracted the `Content-Length` header by iterating through `request.scope.get("headers", [])`. However, it used direct assignment (`content_length = v`), meaning if an attacker provided multiple `Content-Length` headers, the middleware only validated the last one. If an attacker provided a huge payload, set the first `Content-Length` to the true length (which the ASGI server might parse) and the second `Content-Length` to a small value, they could bypass the payload size limit and trigger a Memory Exhaustion DoS.
**Learning:** HTTP allows multiple headers with the same name. Iterating through a list of header tuples and overwriting a variable on match is a critical vulnerability pattern when dealing with security checks, as it allows attackers to hide malicious payloads or bypass validations.
**Prevention:** When extracting headers from an ASGI scope loop for security validation, always concatenate multiple values for the same key using a comma separator (e.g., `content_length += b"," + v`) to ensure all values are evaluated or trigger a parsing error.

## 2026-11-20 - [IP Spoofing Vulnerability via X-Vercel-Forwarded-For Break Statement]
**Vulnerability:** The IP extraction logic iterated through ASGI scope headers and immediately called `break` when it found an `x-vercel-forwarded-for` header. Because attackers can manually inject this header, and proxy infrastructures (like Vercel) append their legitimate header to the list, the `break` statement caused the application to stop parsing and mistakenly trust the attacker's fake IP, enabling them to bypass IP-based rate limiting entirely.
**Learning:** When parsing headers for security validation (like extracting trusted IP addresses from proxy-appended headers), stopping at the first occurrence allows attackers to spoof the value by inserting their payload before the legitimate proxy appends its own.
**Prevention:** When extracting headers from an ASGI scope loop for security validation, never use a `break` statement. Always iterate through all headers, concatenate multiple values for the same key using a comma separator (e.g., `vercel_ip += b"," + v`), and extract the right-most (or structurally defined) value to ensure you are validating the authoritative proxy's header.
