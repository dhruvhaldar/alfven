from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from typing import List
import os
import time
import logging
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
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
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

# 🛡️ Sentinel: Content Security Policy
# Whitelist CDNs used in public/index.html (Three.js, D3, Chart.js, MathJax)
# Removed 'unsafe-eval' as it's not needed for modern library versions used here.
# Added object-src 'none', base-uri 'self', and form-action 'self' for hardening.
CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' https://cdnjs.cloudflare.com https://d3js.org https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self' https://cdn.jsdelivr.net; "
    "connect-src 'self'; "
    "frame-ancestors 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self';"
)


def get_client_ip(request: Request) -> str:
    # 🛡️ Sentinel: Secure IP Extraction
    # If running on Vercel (indicated by VERCEL environment variable),
    # we can trust the X-Forwarded-For header as Vercel ensures it contains the client IP.
    if os.environ.get("VERCEL"):
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

    # Fallback to direct connection IP
    # This is safe if not behind a proxy, or if the ASGI server is configured to handle proxy headers.
    return request.client.host if request.client else "unknown"


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
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})


# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    response.headers["Content-Security-Policy"] = CSP_POLICY

    # 🛡️ Sentinel: HSTS & Permissions Policy
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    return response


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


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/plasma/debye")
def get_debye_length(
    n: float = Query(..., ge=0.1, le=1e30), T_ev: float = Query(..., ge=0.01, le=1e9)
):
    """
    Calculate Debye Length.
    """
    plasma = PlasmaState(n, T_ev)
    return {"debye_length": plasma.debye_length}


@app.get("/api/plasma/parameters")
def get_plasma_parameters(
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
def get_larmor_radius(
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
def get_plasma_frequency(n: float = Query(..., ge=0.1, le=1e30)):
    """
    Calculate Plasma Frequency.
    """
    plasma = PlasmaState(n, 1.0)  # T doesn't matter
    return {"plasma_frequency": plasma.plasma_frequency}


@app.get("/api/solar/parker")
def get_parker_spiral(
    r: float = Query(..., ge=0, le=1e20), v_sw: float = Query(400000, ge=0.1, le=3e8)
):
    """
    Calculate Parker Spiral Angle.
    """
    ps = ParkerSpiral(v_sw=v_sw)
    return {"spiral_angle": ps.spiral_angle(r)}


@app.get("/api/solar/sunspot")
def get_sunspot_temperature(ratio: float = Query(..., ge=0, le=1e4)):
    """
    Estimate Sunspot Temperature.
    """
    T = sunspot_temperature(ratio)
    return {"temperature_k": T}


@app.get("/api/magnetosphere/standoff")
def get_magnetopause_standoff(
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
def get_ionosphere_profile(data: IonosphereInput):
    """
    Get Ionosphere Altitude Profile.
    """
    # Optimize: Create all layers first then construct profile once.
    # This avoids O(N^2) list concatenation in the previous loop implementation.
    layers = [ChapmanLayer(lp.h0, lp.H, lp.n_max) for lp in data.layers]

    if layers:
        profile = ChapmanProfile(layers)
        result = profile.get_profile_data(data.min_h, data.max_h, data.steps)
        return result
    return {"altitude": [], "density": []}


@app.post("/api/aurora/power")
def get_aurora_power(data: AuroraInput):
    """
    Estimate Auroral Power.
    """
    ap = AuroraPower(data.E_field, data.sigma_P, data.area)
    return {"dissipated_power": ap.dissipated_power, "sheet_current": ap.sheet_current}


# Mount static files for local development
if os.path.exists("public"):
    app.mount("/", StaticFiles(directory="public", html=True), name="static")
