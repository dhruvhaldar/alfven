## 2026-05-20 - Rate Limiter Optimization
**Learning:** Periodic cleanup of resources (like rate limiter keys) can cause latency spikes proportional to the number of tracked items (O(N)).
**Action:** Use a continuous, amortized O(1) cleanup strategy. By maintaining a global deque of all request timestamps, we can check only the oldest (expired) requests on each call, eliminating bursty cleanup cycles.

## 2026-05-21 - Rate Limiter LRU Eviction
**Learning:** Evicting the Least Recently Used (LRU) item from a dictionary using `min(d, key=...)` is an O(N) operation, which can become a bottleneck under high load or DoS attacks.
**Action:** Leverage Python 3.7+ insertion-ordered dictionaries. By popping and re-inserting a key upon access, it moves to the end (Most Recently Used). The first key (`next(iter(d))`) then becomes the LRU item, allowing for O(1) eviction.

## 2026-05-22 - Token Bucket Rate Limiting
**Learning:** Storing timestamps for every request (Sliding Window Log) consumes O(N) memory per user and complicates global cleanup, potentially leading to OOM or redundant storage.
**Action:** Use Token Bucket algorithm. It requires only O(1) space (tokens + last_update) per user and strict O(1) time complexity, eliminating the need for a global request log while maintaining rate limits.

## 2026-05-23 - D3.js DOM Thrashing
**Learning:** Clearing an entire SVG with `d3.selectAll("*").remove()` on every update frame causes significant DOM thrashing and layout recalculations, especially for high-frequency inputs like range sliders.
**Action:** Use D3's Enter/Update/Exit pattern (or selection update) to reuse existing SVG elements. Initialize static structure once, and only update attributes of dynamic elements on subsequent calls. This preserves the DOM tree and improves rendering performance.

## 2026-05-24 - Chart.js Instance Reuse
**Learning:** Destroying and recreating Chart.js instances on every data update is a significant performance bottleneck, causing canvas context reallocation and memory churn.
**Action:** Always check for an existing chart instance before creating a new one. If it exists, update its data via `chart.data.datasets[0].data = newData` and call `chart.update()`. This avoids the initialization overhead and provides smoother transitions.

## 2026-05-25 - Python built-in math vs NumPy overhead
**Learning:** Using NumPy functions (`np.sqrt`, `np.arctan`, `np.exp`) on single scalar values is significantly slower (often 2x-3x slower) than using Python's built-in `math` module equivalent (`math.sqrt`, `math.atan`, `math.exp`). NumPy's overhead for argument checking, type coercion, and ufunc dispatch negates its C-level speed advantages when not operating on arrays.
**Action:** When computing properties for single objects (like scalar calculations in `PlasmaState` or `ParkerSpiral`), always use Python's built-in `math` module to eliminate NumPy dispatch overhead. Reserve NumPy exclusively for array operations (like altitude profiles).

## 2026-05-26 - API Response Compression
**Learning:** Returning large, uncompressed arrays (like altitude profiles) as JSON strings consumes significant network bandwidth.
**Action:** Use GZip compression (`GZipMiddleware` in FastAPI) to drastically reduce the network transfer size of large JSON payloads, improving load times.

## 2026-03-03 - NumPy sum optimization over arrays
**Learning:** In Python, iterating over a small list of layers and repeatedly calling `total_n += layer.density(h)` where `total_n` and the result are numpy arrays is slow due to the creation of intermediate arrays and repeated Python loop overhead.
**Action:** Use Python's built-in `sum()` with a list comprehension (`sum([layer.density(h) for layer in self.layers])`). It is ~3x faster than initializing `np.zeros_like(h)` and accumulating in a loop for a small number of layers.

## 2026-03-04 - Render-Blocking JavaScript Optimization
**Learning:** Synchronous `<script>` tags in the HTML `<head>` (like large CDNs for Three.js, D3.js, Chart.js) severely block the browser's main thread and delay First Contentful Paint (FCP).
**Action:** Add the `defer` attribute to all external scripts in the `<head>`. Crucially, to maintain execution order and avoid `undefined` variable errors, any local `<script>` tags later in the document that depend on these libraries must also have the `defer` attribute.

## 2026-06-03 - Deterministic API Client-Side Caching
**Learning:** Toggling UI states that depend on a small, discrete set of inputs (e.g., a simple Day/Night toggle) can trigger redundant network requests and server-side recalculations if not cached, increasing latency and server load.
**Action:** Implement a client-side cache (`const cache = {}`) to store the responses for deterministic API calls with minimal input spaces. Always check the cache first before updating loading states or triggering `fetch` to ensure instant UI responsiveness.

## 2026-08-01 - Redundant API Calls on Slider Revisit
**Learning:** When using slider inputs (like range sliders for density, velocity, or sunspot ratio) to control API-driven data updates, users frequently scrub back and forth over the same values. This causes rapid, redundant API requests for previously calculated data, wasting bandwidth and backend processing even when debouncing is implemented.
**Action:** Use an in-memory client-side dictionary cache (`const cache = {}`) keyed by the active parameters. Always check the cache before updating loading states or calling `fetch`. If cached, update the UI synchronously and immediately, providing a far more responsive UX without network delay.

## 2026-08-02 - Fast os.environ Lookup Avoidance
**Learning:** `os.environ.get()` in Python involves function call overhead and dictionary traversal of the environment variables mapped at startup. While not I/O bound, when placed in middleware or per-request logic (like `get_client_ip`), evaluating this on every incoming request adds unnecessary overhead.
**Action:** Evaluate static environment flags (e.g., `IS_VERCEL = bool(os.environ.get("VERCEL"))`) once at the module level (during cold start) rather than on every request. Caching this boolean improves the function execution speed by nearly ~8x.

## 2026-08-03 - Prevent DOM Thrashing on Cached High-Frequency UI Events
**Learning:** During high-frequency UI events like dragging a range slider, triggering loading spinners and relying on debouncing causes significant DOM thrashing and noticeable visual delays (due to `createElement`, layout reflows), even if the result is already in the client-side cache and the network call would be skipped later.
**Action:** Before applying any transient loading states (`createElement`, `textContent`) or scheduling a debounced function, synchronously check the client-side cache for the current parameters. Additionally, verify if the container's `aria-busy` state is already set to prevent redundant DOM updates. If cached, call the update function directly for immediate, jank-free rendering.

## 2026-10-24 - Precomputing Mathematical Constants
**Learning:** Re-evaluating expressions involving fundamental physical constants (e.g., `e`, `eps_0`, `m_e`) dynamically on every property access introduces redundant calculation overhead, especially noticeable in math-heavy backend properties. Furthermore, Python's exponentiation operator (`**2`) has minor overhead compared to direct multiplication.
**Action:** Precompute these mathematical combinations at the module level when possible. Additionally, replace small integer power operators like `x**2` with direct multiplication (`x * x`) to optimize calculation-intensive properties.

## 2026-10-25 - Precomputing Constants Across Domains
**Learning:** In physics calculations, mathematical constants (`B0^2 / (mu_0 * m_p)`) spread across different domains (e.g., magnetic field, vacuum permeability, proton mass) are often repeatedly evaluated at runtime. This causes unnecessary overhead on each property access, and standard exponentiation like `v**2` is slower than `v*v`.
**Action:** Always extract and combine static parameters into precomputed module-level constants. Replace operations like `v**2` with direct multiplication `v*v`. This optimization (applied to `Magnetopause.radius_re`) reduces execution time by ~50% (0.46μs to 0.23μs) per call.

## 2026-10-26 - Precomputing Constants for Object Initialization
**Learning:** Evaluating combinations of physical constants (like `e / k_B`) inside an object's `__init__` method introduces redundant calculation overhead on every instantiation. This adds up when objects are created frequently (e.g., per API request).
**Action:** Precompute these constant combinations at the module level. Ensure that attributes which were previously calculated dynamically (like `self.T_k`) are preserved using the precomputed constants to maintain backwards compatibility without the performance penalty.

## 2026-10-27 - NumPy isscalar Overhead Avoidance
**Learning:** `np.isscalar()` has significant function call and type-checking overhead compared to Python's built-in `isinstance()`. When placed in heavily called mathematical logic (like ionosphere density calculations over arrays), `np.isscalar()` slows down execution—my benchmarks showed `isinstance` is ~4x faster for array-like inputs and moderately faster for scalar inputs.
**Action:** Replace `np.isscalar(x)` with `isinstance(x, (int, float, np.number))` for better performance. This reliably captures built-in Python scalars as well as NumPy scalar types with much lower overhead.

## 2026-10-28 - Algebraic Expansion to Reduce Costly Operations Inside Exponential Functions
**Learning:** In heavily called complex mathematical models (like `ChapmanLayer` density where `n(h) = n_max * exp(0.5 * (1 - z - exp(-z)))`), directly computing terms like `1` minus terms adds redundant scalar operations, and evaluating `exp(0.5)` each time multiplies redundant costs. A mathematically equivalent expansion, `exp(0.5) * exp(-0.5 * (z + exp(-z)))`, simplifies the expression inside the exponent.
**Action:** Use algebraic expansion to pull constants out of mathematical functions and precompute them during `__init__` (e.g. `_n_max_exp_half = n_max * math.exp(0.5)`). Apply the algebraically simplified formula `_n_max_exp_half * exp(-0.5 * (z + exp(-z)))` inside the heavily called methods to reduce unnecessary floating-point operations.

## 2026-10-29 - Avoid request.url in ASGI Middleware
**Learning:** In Starlette/FastAPI, accessing `request.url` (e.g., `request.url.path`) instantiates a new `URL` object, which is a relatively expensive operation when executed on every request in middleware.
**Action:** To check the request path in middleware, read directly from the ASGI scope dictionary using `request.scope["path"]`. This avoids the object instantiation overhead and is significantly faster.

## 2026-11-01 - Avoid Sum with NumPy Arrays
**Learning:** In Python, iterating over a list of arrays and summing them with the built-in `sum()` function is computationally slow. It initializes multiple temporary objects and causes significant memory allocation and deallocation overhead.
**Action:** When computing sums across multiple arrays (like in `ChapmanProfile.density`), initialize the result array using `.copy()` on the first element, and iterate through the remaining elements using in-place addition (`+=`). This avoids allocating temporary arrays and is noticeably faster, saving ~4-5% execution time.

## 2026-11-02 - FastAPI Threadpool Overhead on CPU-Bound Fast Endpoints
**Learning:** In FastAPI, synchronous endpoints (defined with `def`) are executed in a separate threadpool to prevent blocking the async event loop. For endpoints that perform very fast, purely CPU-bound calculations (like mathematical formulas), the context-switching and offloading overhead can take longer than the calculation itself, introducing a measurable performance penalty.
**Action:** Refactor extremely fast, non-blocking CPU-bound endpoints to be asynchronous (`async def`). This forces FastAPI to execute them directly on the main event loop, bypassing the threadpool and improving throughput (benchmark showed ~10-15% speedup for rapid requests).

## 2026-11-03 - NumPy Broadcasting over Multiple Objects
**Learning:** When calculating combined results of multiple objects over an array of inputs (like evaluating multiple atmospheric layers across a range of altitudes), sequentially calling each object's method in a Python loop creates intermediate arrays and involves significant Python iteration overhead.
**Action:** Extract the properties into NumPy arrays, expand their dimensions with `np.newaxis` to allow broadcasting, and perform vectorized in-place mathematical operations. Sum across the object axis (`np.sum(axis=0)`) at the end to eliminate loop overhead and drastically reduce intermediate allocations.

## 2026-11-04 - Precomputing Linear Transformation Constants
**Learning:** Calculating `z = (h - h0) / H` inside a heavily called function takes slightly longer due to the subtraction and division. Replacing it with `z = h * (1/H) - (h0/H)` allows precomputing the inverse and the constant offset term `(h0/H)`, leading to faster execution for scalar and array inputs.
**Action:** Algebraically expand linear transformations to precompute constants, reducing operations inside heavily called functions like `density`.

## 2026-11-05 - Precomputing Instance-Specific Derived Terms
**Learning:** While static physical constants can be precomputed at the module level, dynamically calculating instance-specific derived variables (such as square roots of object attributes) on every property access still incurs significant overhead. If these base attributes are mutable, developers often hesitate to precompute them in `__init__` for fear of state drift.
**Action:** Use Python `@property` setters for mutable instance variables to automatically update precomputed derived terms (like square roots) alongside the base values. This guarantees state consistency while eliminating redundant, expensive mathematical function calls during heavy property accesses.

## 2026-11-06 - Avoid request.client Instantiation Overhead
**Learning:** In Starlette/FastAPI, accessing `request.client` (e.g., `request.client.host`) in middleware or frequently called helper functions like `get_client_ip` introduces performance overhead by instantiating an `Address` namedtuple for every request.
**Action:** To extract the client IP faster, read directly from the ASGI scope using `request.scope.get("client")[0]` instead. Ensure a fallback using `hasattr(request, "scope")` is provided for mocked requests in test environments. This bypasses the object instantiation overhead and improves execution time by ~86%.

## 2026-11-07 - Avoid list comprehension overhead in sum()
**Learning:** In performance-critical paths involving scalar accumulation (e.g., calculating scalar density across multiple atmospheric layers), passing a list comprehension to the built-in `sum()` function (`sum([obj.val(x) for obj in items])`) creates and destroys a temporary list in memory, causing measurable allocation and iteration overhead compared to a plain loop.
**Action:** Replace `sum([obj.val(x) for obj in items])` with a standard `for` loop and an accumulator variable for small sequences where creating a temporary list is unnecessary.

## 2026-11-08 - Avoid isinstance tuple overhead in hot paths
**Learning:** `isinstance(x, (int, float, np.number))` creates an implicit loop checking the tuple of types. In extremely hot mathematical paths, checking the exact type of built-ins first via `type(x) in (int, float)` followed by `isinstance` for numpy scalars is noticeably faster due to short-circuiting and bypassing the tuple checking machinery.
**Action:** In highly optimized numerical code, use `type(x) in (int, float) or isinstance(x, np.number)` instead of `isinstance(x, (int, float, np.number))` to save fractions of a microsecond per call.

## 2026-11-09 - Avoid redundant DOM queries during rapid input events
**Learning:** During high-frequency UI events like dragging a range slider or rapid typing, executing expensive DOM queries (like `querySelectorAll`) and modifying attributes repeatedly causes significant layout thrashing and measurable UI lag.
**Action:** Before applying a visual state change (such as a 'stale' state) and modifying child elements, check if the parent container already has the target state class (e.g., `!resultsEl.classList.contains('stale-results')`). This ensures the expensive DOM manipulations only run once per state transition.

## 2026-11-10 - Avoid redundant layout thrashing during rapid DOM updates
**Learning:** Calling `getBoundingClientRect()` forces the browser to synchronously recalculate layout. When placed inside a function that runs frequently (like `drawMagnetosphere` during rapid slider input), it causes measurable rendering jank.
**Action:** Extract `getBoundingClientRect()` from rapid render loops. Cache container dimensions globally, initialize them on `DOMContentLoaded`, and only update them via a `window.addEventListener('resize')` handler.
## 2026-11-11 - Precomputed Dictionary Update For Static Headers
**Learning:** Assigning multiple static security headers to a dictionary one by one via direct indexing (`headers["key"] = "value"`) on every API request introduces unnecessary Python overhead in execution time, particularly in high-throughput middleware like `add_security_headers`.
**Action:** Extract these invariant header values into a module-level precomputed dictionary (`_STATIC_SECURITY_HEADERS`) and use `headers.update()` instead. Benchmarks indicate this reduces dictionary population time by ~40% for these static assignments, serving as a minor but compounding micro-optimization per request.

## 2026-11-12 - Form Submission Caching
**Learning:** For deterministic mathematical calculators triggered by manual form submissions (unlike slider-driven inputs which often have debounce or caching implemented), users frequently double-click or re-calculate the exact same parameters. This causes unnecessary network requests to the API and delays rendering.
**Action:** Implement an in-memory client-side dictionary cache keyed by the concatenated input parameters (e.g., `${n}_${T}`) for form-based queries. Before making the `fetch` call, check the cache; if a hit occurs, immediately update the DOM to instantly resolve the request.

## 2026-11-13 - Scratchpad Cleanup
**Learning:** Leaving temporary performance test scripts (like `test_perf.py`) in the workspace during a pull request clutters the repository and fails code review.
**Action:** When creating temporary performance benchmark scripts to measure optimizations, ensure they are completely deleted from the workspace using `rm` before requesting a code review or committing.

## 2026-11-14 - Lazy Initialization of Instance Properties
**Learning:** While static physical constants should be precomputed at the module level, eagerly precomputing instance-specific derived mathematical terms (like square roots of attributes) in `@property` setters introduces redundant overhead. If the object state is rapidly updated but the derived physical properties are only accessed occasionally, the computation in the setter is wasted.
**Action:** Use lazy initialization for expensive derived properties. Set the internal cache variables to `None` upon attribute assignment (e.g. in the setter), and only compute and cache the value upon its first access in the getter method. This drastically minimizes overhead during object instantiation and rapid state updates, speeding up execution significantly when all properties aren't accessed simultaneously.
## 2026-11-15 - Array Compatibility vs Math Module
**Learning:** In scientific Python codebases, replacing native arithmetic operators (like `x**0.25`) with `math` module functions (like `math.sqrt`) for micro-optimization can break vectorization, because `math` functions only accept scalars and throw `TypeError` when passed NumPy arrays.
**Action:** Avoid replacing arithmetic operators with `math` functions in numerical code unless explicitly dealing with known scalars and where the performance gain outweighs the loss of array compatibility.
## 2026-11-16 - Avoid Intermediate Array Allocation in NumPy Functions
**Learning:** When executing mathematical functions over NumPy arrays (like `np.exp(-z)`), Python first allocates a new array to store the result of `-z`, and then allocates a second new array for the output of `np.exp()`. The intermediate array is immediately discarded, wasting time on memory allocation.
**Action:** In performance-critical NumPy operations, avoid intermediate arrays by explicitly separating operations and using the `out=` parameter. For example, allocate the first array via `term = np.negative(z)` and then perform the next operation in-place: `np.exp(term, out=term)`.
## 2026-11-17 - Avoid isinstance tuple overhead in hot paths while preserving subclass polymorphism
**Learning:** In CPython, `isinstance(obj, (type1, type2))` is highly optimized in C and short-circuits instantly, and should generally not be replaced with `type(obj) in (type1, type2)` as it breaks subclass polymorphism. However, in extremely hot mathematical paths checking against both built-ins and NumPy types, using `type(x) in (int, float) or isinstance(x, np.number)` is faster as it bypasses the tuple checking machinery for common built-ins while preserving subclass polymorphism for NumPy scalars.
**Action:** In highly optimized numerical code, use `type(x) in (int, float) or isinstance(x, np.number)` instead of `isinstance(x, (int, float, np.number))` to save fractions of a microsecond per call, but avoid `type() in` checks generally elsewhere to preserve Python's subclassing mechanics.

## 2026-11-18 - Avoid Intermediate Array Allocation in NumPy Functions (Refinement)
**Learning:** When optimizing chained NumPy array expressions (e.g., `np.exp(-0.5 * (z + np.exp(-z)))`), explicitly allocating a single temporary array (`term = np.negative(z)`) and using in-place operations (`np.exp(term, out=term)`, `term += z`) reduces intermediate memory allocations and improves execution speed. However, you must ensure the input is strictly an array, as in-place `out=` parameters will crash on scalars.
**Action:** In performance-critical NumPy operations, avoid intermediate arrays by explicitly separating operations and using the `out=` parameter. For example, allocate the first array via `term = np.negative(z)` and then perform the next operation in-place: `np.exp(term, out=term)`.

## 2026-11-19 - Precomputed Dictionary Update For Dynamic Header Modifications
**Learning:** Even when using a precomputed dictionary (`_STATIC_SECURITY_HEADERS`) to efficiently populate common headers via `dict.update()`, making subsequent individual dictionary assignments (like `headers["Cache-Control"] = ...`) for conditional cases (such as API-only responses) still introduces measurable overhead per request.
**Action:** When a conditionally executed branch reliably adds a specific set of extra properties (like `Cache-Control` for APIs), precompute a complete alternative dictionary (`_STATIC_API_SECURITY_HEADERS = _STATIC_SECURITY_HEADERS.copy()`) that includes both base and branch-specific keys. Using `dict.update()` with the correct fully-precomputed dictionary inside the conditional logic is faster than applying a base dictionary and appending extra keys manually.
