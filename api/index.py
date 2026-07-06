from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field, field_validator
from typing import List
import math
import os
import time
import logging
import urllib.parse
from alfven import (
    PlasmaState,
    ParkerSpiral,
    Magnetopause,
    ChapmanLayer,
    ChapmanProfile,
    AuroraPower,
    sunspot_temperature,
)

app = FastAPI(
    title="Alfven API", description="Space Weather & Plasma Physics Simulator API"
)

# Optimization: Compress large responses (e.g., Ionosphere profile data)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configure logging
logger = logging.getLogger("alfven")


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # 🛡️ Sentinel: Log the exception with traceback for debugging/auditing
    logger.error("Unhandled exception: %s", exc, exc_info=True)

    response = JSONResponse(
        status_code=500, content={"detail": "Internal Server Error"}
    )
    is_api = request.scope.get("path", "").startswith("/api/")
    apply_security_headers_to_dict(response.headers, is_api)
    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # 🛡️ Sentinel: Sanitize validation errors to prevent reflection of malicious input
    sanitized_errors = []
    for err in exc.errors():
        err_copy = dict(err)
        err_copy.pop("input", None)
        err_copy.pop("url", None)
        sanitized_errors.append(err_copy)

    response = JSONResponse(
        status_code=422,
        content={"detail": jsonable_encoder(sanitized_errors)}
    )
    is_api = request.scope.get("path", "").startswith("/api/")
    apply_security_headers_to_dict(response.headers, is_api)
    return response

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Pass along existing headers (like WWW-Authenticate)
    headers = getattr(exc, "headers", None)
    if headers:
        response = JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=headers
        )
    else:
        response = JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    is_api = request.scope.get("path", "").startswith("/api/")
    apply_security_headers_to_dict(response.headers, is_api)
    return response


# Rate Limiting
# 🛡️ Sentinel: Rate Limiting
# Simple in-memory rate limiter to prevent DoS
# Optimization: Use Token Bucket for O(1) time and O(1) space per user
request_counts = {}  # Dict[str, List[float]] -> [tokens, last_updated]

RATE_LIMIT = 100  # requests per minute
WINDOW_SIZE = 60  # seconds
REFILL_RATE = RATE_LIMIT / WINDOW_SIZE # tokens per second
MAX_IPS = 2000    # Maximum number of tracked IPs to prevent memory exhaustion

# Optimization: Cache Vercel environment variable to avoid slow os.environ lookups on every request
IS_VERCEL = bool(os.environ.get("VERCEL"))

# 🛡️ Sentinel: Content Security Policy
# Whitelist CDNs used in public/index.html (Three.js, D3, Chart.js, MathJax)
# Removed 'unsafe-eval' as it's not needed for modern library versions used here.
# Added object-src 'none', base-uri 'self', and form-action 'self' for hardening.
CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' https://cdnjs.cloudflare.com https://d3js.org https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "upgrade-insecure-requests;"
)


_STATIC_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": CSP_POLICY,
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin"
}

# Optimization: Precompute API-specific headers to eliminate individual dictionary assignments on every API request
_STATIC_API_SECURITY_HEADERS = _STATIC_SECURITY_HEADERS.copy()
_STATIC_API_SECURITY_HEADERS.update({
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache"
})

def apply_security_headers_to_dict(headers: dict, is_api: bool):
    # 🛡️ Sentinel: Remove Server Header to obscure technology stack
    if "server" in headers:
        del headers["server"]

    # Optimization: Use dict.update() with precomputed static headers to avoid redundant individual assignments
    if is_api:
        headers.update(_STATIC_API_SECURITY_HEADERS)
    else:
        headers.update(_STATIC_SECURITY_HEADERS)


def get_client_ip(request: Request) -> str:
    # 🛡️ Sentinel: Secure IP Extraction
    # If running on Vercel (indicated by VERCEL environment variable),
    # we can trust the X-Forwarded-For header as Vercel ensures it contains the client IP.
    raw_ip = "unknown"
    if IS_VERCEL:
        # Optimization: Extract headers directly from ASGI scope to avoid `request.headers`
        # dict instantiation overhead which iterates and parses the entire tuple list.
        vercel_ip = None
        forwarded = None
        if hasattr(request, "scope"):
            for k, v in request.scope.get("headers", []):
                if k == b"x-vercel-forwarded-for":
                    vercel_ip = v.decode("latin1")
                    break
                elif k == b"x-forwarded-for":
                    forwarded = v.decode("latin1")

        # 🛡️ Sentinel: Prefer Vercel's platform-specific non-spoofable header if available
        if vercel_ip:
            raw_ip = vercel_ip.strip()
        elif forwarded:
            # 🛡️ Sentinel: Proxies append to X-Forwarded-For. The right-most IP is the real client.
            # Taking the first IP allows an attacker to spoof their IP and bypass rate limits.
            raw_ip = forwarded.split(",")[-1].strip()

    if raw_ip == "unknown":
        # Fallback to direct connection IP
        # This is safe if not behind a proxy, or if the ASGI server is configured to handle proxy headers.
        # Optimization: Read IP directly from ASGI scope to avoid `Address` namedtuple instantiation overhead
        if hasattr(request, "scope"):
            client = request.scope.get("client")
            if client:
                raw_ip = client[0]
        elif getattr(request, "client", None):
            raw_ip = request.client.host

    # 🛡️ Sentinel: Limit IP string length to prevent Memory Exhaustion DoS
    # Max IPv6 length is 45 characters. Truncate to 45 characters.
    return str(raw_ip)[:45]


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # 🛡️ Sentinel: Enhanced IP extraction
    # Use helper to securely extract IP based on environment context.
    client_ip = get_client_ip(request)

    # Optimization: Use monotonic time for robust rate limiting regardless of system clock changes
    now = time.monotonic()

    # Rate Limit Logic (Token Bucket)
    if client_ip in request_counts:
        # Refresh LRU position by moving accessed key to the end
        bucket = request_counts.pop(client_ip)
        request_counts[client_ip] = bucket

        # Refill tokens based on elapsed time
        tokens, last_update = bucket
        elapsed = now - last_update
        if elapsed < 0: elapsed = 0 # Safety against clock skew

        # Refill tokens up to capacity
        tokens = min(RATE_LIMIT, tokens + elapsed * REFILL_RATE)

        # Update bucket state
        bucket[0] = tokens
        bucket[1] = now
    else:
        # Hard limit safeguard
        if len(request_counts) >= MAX_IPS:
            # 🛡️ Sentinel: Evict the Least Recently Used IP
            # Optimization: Use O(1) eviction by relying on Python's insertion-ordered dicts.
            try:
                lru_ip = next(iter(request_counts))
                del request_counts[lru_ip]
            except StopIteration:
                pass

        # New bucket starts full
        tokens = RATE_LIMIT
        bucket = [tokens, now]
        request_counts[client_ip] = bucket

    # Consume token
    if bucket[0] >= 1:
        bucket[0] -= 1
        return await call_next(request)
    else:
        # 🛡️ Sentinel: Log security event (Rate Limit Exceeded)
        # Optimization: Use request.scope.get("path") instead of request.url.path to avoid expensive URL instantiation
        path = request.scope.get("path", "") if hasattr(request, "scope") else "unknown"

        # 🛡️ Sentinel: Sanitize path to prevent Log Injection/Forging
        if isinstance(path, str):
            path = urllib.parse.unquote(path).replace("\n", "\\n").replace("\r", "\\r")

        # 🛡️ Sentinel: Sanitize IP to prevent Log Injection/Forging
        if isinstance(client_ip, str):
            client_ip = urllib.parse.unquote(client_ip).replace("\n", "\\n").replace("\r", "\\r")

        logger.warning(f"Rate limit exceeded for IP: {client_ip} on path: {path}")
        # 🛡️ Sentinel: Add Retry-After header to 429 response
        wait_time = math.ceil((1 - bucket[0]) / REFILL_RATE)
        response = JSONResponse(
            status_code=429,
            content={"detail": "Too many requests"},
            headers={"Retry-After": str(wait_time)}
        )
        is_api = request.scope.get("path", "").startswith("/api/") if hasattr(request, "scope") else False
        apply_security_headers_to_dict(response.headers, is_api)
        return response


# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    is_api = request.scope.get("path", "").startswith("/api/")
    apply_security_headers_to_dict(response.headers, is_api)

    return response


# Request Size Limit Middleware
@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    # 🛡️ Sentinel: Enforce maximum request body size to prevent Memory Exhaustion DoS
    if request.method in ("POST", "PUT", "PATCH"):
        response = None

        # Optimization: Extract headers directly from ASGI scope to avoid `request.headers`
        # dict instantiation overhead which iterates and parses the entire tuple list.
        transfer_encoding = b""
        content_length = None
        if hasattr(request, "scope"):
            for k, v in request.scope.get("headers", []):
                if k == b"transfer-encoding":
                    transfer_encoding = v
                elif k == b"content-length":
                    content_length = v

        if b"chunked" in transfer_encoding.lower():
            response = JSONResponse(status_code=411, content={"detail": "Chunked encoding not supported"})
        else:
            if content_length is not None:
                try:
                    if int(content_length) > 102400:  # 100 KB limit
                        response = JSONResponse(
                            status_code=413,
                            content={"detail": "Payload Too Large"}
                        )
                except ValueError:
                    response = JSONResponse(
                        status_code=400,
                        content={"detail": "Invalid Content-Length header"}
                    )
            else:
                # 🛡️ Sentinel: Reject requests missing Content-Length to prevent bypassing body size limits
                response = JSONResponse(
                    status_code=411,
                    content={"detail": "Length Required"}
                )

        if response is not None:
            is_api = request.scope.get("path", "").startswith("/api/") if hasattr(request, "scope") else False
            apply_security_headers_to_dict(response.headers, is_api)
            return response

    return await call_next(request)


# Input Models


class PlasmaInput(BaseModel):
    n: float = Field(..., ge=0.1, le=1e30)
    T_ev: float = Field(..., ge=0.01, le=1e9)


class LarmorInput(BaseModel):
    T_ev: float = Field(..., ge=0.01, le=1e9)
    B: float = Field(..., ge=1e-12, le=1e5, description="Cannot be 0")


class SolarInput(BaseModel):
    v_sw: float = Field(..., ge=0.1, le=3e8)
    r: float = Field(..., ge=0, le=1e20)


class MagnetosphereInput(BaseModel):
    density: float = Field(..., ge=0.1, le=1e30)
    velocity: float = Field(..., ge=0.1, le=3e8)
    Bz: float = Field(0, le=1e5, ge=-1e5)


class LayerParams(BaseModel):
    h0: float = Field(..., ge=0, le=10000)
    H: float = Field(..., gt=0, le=5000)
    n_max: float = Field(..., gt=0, le=1e30)


class IonosphereInput(BaseModel):
    layers: List[LayerParams]
    min_h: float = Field(..., ge=0, le=10000)
    max_h: float = Field(..., gt=0, le=10000)
    steps: int = Field(100, gt=0, le=2000)

    @field_validator("layers")
    @classmethod
    def check_layers_limit(cls, v):
        if len(v) > 20:
            raise ValueError("Too many layers (max 20)")
        return v


class AuroraInput(BaseModel):
    E_field: float = Field(..., le=1e9)
    sigma_P: float = Field(..., ge=1e-5, le=1e6)
    area: float = Field(..., ge=1e-5, le=1e20)


# Endpoints


# Optimization: Make endpoints async so they run directly on the event loop.
# Since these are fast, CPU-bound calculations, doing them sync would offload them
# to FastAPI's threadpool, which introduces a ~10-15% performance penalty due to overhead.
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/plasma/debye")
async def get_debye_length(
    n: float = Query(..., ge=0.1, le=1e30), T_ev: float = Query(..., ge=0.01, le=1e9)
):
    """
    Calculate Debye Length.
    """
    plasma = PlasmaState(n, T_ev)
    return {"debye_length": plasma.debye_length}


@app.get("/api/plasma/parameters")
async def get_plasma_parameters(
    n: float = Query(..., ge=0.1, le=1e30), T_ev: float = Query(..., ge=0.01, le=1e9)
):
    """
    Calculate both Debye Length and Plasma Frequency.
    """
    plasma = PlasmaState(n, T_ev)
    return {
        "debye_length": plasma.debye_length,
        "plasma_frequency": plasma.plasma_frequency,
    }


@app.get("/api/plasma/larmor")
async def get_larmor_radius(
    T_ev: float = Query(..., ge=0.01, le=1e9),
    B: float = Query(..., ge=1e-12, le=1e5),
):
    """
    Calculate Larmor Radius.
    """
    if B == 0:
        raise HTTPException(status_code=422, detail="B cannot be 0")

    # Use dummy density n=1e6 since it doesn't affect Larmor radius
    plasma = PlasmaState(1e6, T_ev)
    return {"larmor_radius": plasma.larmor_radius(B)}


@app.get("/api/plasma/frequency")
async def get_plasma_frequency(n: float = Query(..., ge=0.1, le=1e30)):
    """
    Calculate Plasma Frequency.
    """
    plasma = PlasmaState(n, 1.0)  # T doesn't matter
    return {"plasma_frequency": plasma.plasma_frequency}


@app.get("/api/solar/parker")
async def get_parker_spiral(
    r: float = Query(..., ge=0, le=1e20), v_sw: float = Query(400000, ge=0.1, le=3e8)
):
    """
    Calculate Parker Spiral Angle.
    """
    ps = ParkerSpiral(v_sw=v_sw)
    return {"spiral_angle": ps.spiral_angle(r)}


@app.get("/api/solar/sunspot")
async def get_sunspot_temperature(ratio: float = Query(..., ge=0, le=1e4)):
    """
    Estimate Sunspot Temperature.
    """
    T = sunspot_temperature(ratio)
    return {"temperature_k": T}


@app.get("/api/magnetosphere/standoff")
async def get_magnetopause_standoff(
    density: float = Query(..., ge=0.1, le=1e30),
    velocity: float = Query(..., ge=0.1, le=3e8),
    Bz: float = Query(0, le=1e5, ge=-1e5),
):
    """
    Calculate Magnetopause Standoff Distance.
    """
    mp = Magnetopause(density, velocity, Bz)
    return {"radius_re": mp.radius_re}


@app.post("/api/ionosphere/profile")
async def get_ionosphere_profile(data: IonosphereInput):
    """
    Get Ionosphere Altitude Profile.
    """
    # Optimize: Create all layers first then construct profile once.
    # This avoids O(N^2) list concatenation in the previous loop implementation.
    layers = [ChapmanLayer(lp.h0, lp.H, lp.n_max) for lp in data.layers]

    if layers:
        profile = ChapmanProfile(layers)
        result = profile.get_profile_data(data.min_h, data.max_h, data.steps)
        # Optimization: Explicitly return JSONResponse to bypass fastapi's recursive jsonable_encoder
        # on large arrays. The lists of floats are already natively JSON serializable.
        # This speeds up large payload serialization significantly.
        return JSONResponse(content=result)

    # Optimization: Also bypass jsonable_encoder for empty fallback
    return JSONResponse(content={"altitude": [], "density": []})


@app.post("/api/aurora/power")
async def get_aurora_power(data: AuroraInput):
    """
    Estimate Auroral Power.
    """
    ap = AuroraPower(data.E_field, data.sigma_P, data.area)
    return {"dissipated_power": ap.dissipated_power, "sheet_current": ap.sheet_current}


# Mount static files for local development
if os.path.exists("public"):
    app.mount("/", StaticFiles(directory="public", html=True), name="static")
