from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from typing import List
import os
import time
import logging
from collections import defaultdict, deque
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
# Optimization: Use deque for O(1) appends and pops
request_counts = defaultdict(deque)
# Global log for O(1) continuous cleanup
# Stores (timestamp, ip) tuples for all requests
request_log = deque()

RATE_LIMIT = 100  # requests per minute
WINDOW_SIZE = 60  # seconds
MAX_IPS = 2000    # Maximum number of tracked IPs to prevent memory exhaustion

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # ⚠️ Warning: In a production environment behind a reverse proxy, request.client.host
    # might be the proxy's IP. A secure implementation should handle X-Forwarded-For
    # with a trusted proxy list.

    # 🛡️ Sentinel: Enhanced IP extraction
    # Try to get the real IP from X-Forwarded-For if available, but be aware of spoofing.
    # We prioritize the LAST IP in the list as trusted proxies/LBs usually append the connecting IP there.
    # Trusting the first IP allows clients to spoof their IP by sending a fake X-Forwarded-For header.
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[-1].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    now = time.time()

    # 1. Continuous Cleanup (Amortized O(1))
    # Remove expired requests from the global log and update user counts
    # This avoids the O(N) iteration over all IPs that was previously done periodically
    while request_log:
        # Check the oldest request in the system
        old_ts, old_ip = request_log[0]
        if now - old_ts > WINDOW_SIZE:
            request_log.popleft()

            # Clean up the specific user's deque if they are still tracked
            if old_ip in request_counts:
                dq = request_counts[old_ip]
                # Remove expired timestamps for this user
                # Since deques are sorted by time, we can just pop from left
                while dq and now - dq[0] > WINDOW_SIZE:
                    dq.popleft()

                # If user has no more valid requests, remove from tracking map
                if not dq:
                    del request_counts[old_ip]
        else:
            # If the oldest request hasn't expired, no other request has
            break

    # 2. Hard limit safeguard
    if len(request_counts) > MAX_IPS:
        # If still over limit, clear the whole cache to prevent OOM.
        # This is a fail-safe.
        request_counts.clear()
        request_log.clear()

    # Rate Limit Logic
    dq = request_counts[client_ip]
    # Note: cleanup above handles general expiry, but checking here is cheap double-check
    # specifically for the current user to ensure absolute precision
    while dq and now - dq[0] > WINDOW_SIZE:
        dq.popleft()

    if len(dq) >= RATE_LIMIT:
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})

    dq.append(now)
    request_log.append((now, client_ip))

    return await call_next(request)


# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # 🛡️ Sentinel: Content Security Policy
    # Whitelist CDNs used in public/index.html (Three.js, D3, Chart.js, MathJax)
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com https://d3js.org https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self' https://cdn.jsdelivr.net; "
        "connect-src 'self'; "
        "frame-ancestors 'self';"
    )
    response.headers["Content-Security-Policy"] = csp_policy

    # 🛡️ Sentinel: HSTS & Permissions Policy
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    return response


# Input Models


class PlasmaInput(BaseModel):
    n: float = Field(..., gt=0)
    T_ev: float = Field(..., gt=0)


class LarmorInput(BaseModel):
    T_ev: float = Field(..., gt=0)
    B: float = Field(..., description="Cannot be 0")


class SolarInput(BaseModel):
    v_sw: float = Field(..., gt=0)
    r: float = Field(..., ge=0)


class MagnetosphereInput(BaseModel):
    density: float = Field(..., gt=0)
    velocity: float = Field(..., gt=0)
    Bz: float = 0


class LayerParams(BaseModel):
    h0: float = Field(..., ge=0)
    H: float = Field(..., gt=0)
    n_max: float = Field(..., gt=0)


class IonosphereInput(BaseModel):
    layers: List[LayerParams]
    min_h: float = Field(..., ge=0)
    max_h: float = Field(..., gt=0)
    steps: int = Field(100, gt=0, le=2000)

    @field_validator("layers")
    @classmethod
    def check_layers_limit(cls, v):
        if len(v) > 20:
            raise ValueError("Too many layers (max 20)")
        return v


class AuroraInput(BaseModel):
    E_field: float
    sigma_P: float = Field(..., gt=0)
    area: float = Field(..., gt=0)


# Endpoints


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/plasma/debye")
def get_debye_length(n: float = Query(..., gt=0), T_ev: float = Query(..., gt=0)):
    """
    Calculate Debye Length.
    """
    plasma = PlasmaState(n, T_ev)
    return {"debye_length": plasma.debye_length}


@app.get("/api/plasma/parameters")
def get_plasma_parameters(n: float = Query(..., gt=0), T_ev: float = Query(..., gt=0)):
    """
    Calculate both Debye Length and Plasma Frequency.
    """
    plasma = PlasmaState(n, T_ev)
    return {
        "debye_length": plasma.debye_length,
        "plasma_frequency": plasma.plasma_frequency,
    }


@app.get("/api/plasma/larmor")
def get_larmor_radius(T_ev: float = Query(..., gt=0), B: float = Query(...)):
    """
    Calculate Larmor Radius.
    """
    if B == 0:
        raise HTTPException(status_code=422, detail="B cannot be 0")

    # Use dummy density n=1e6 since it doesn't affect Larmor radius
    plasma = PlasmaState(1e6, T_ev)
    return {"larmor_radius": plasma.larmor_radius(B)}


@app.get("/api/plasma/frequency")
def get_plasma_frequency(n: float = Query(..., gt=0)):
    """
    Calculate Plasma Frequency.
    """
    plasma = PlasmaState(n, 1.0)  # T doesn't matter
    return {"plasma_frequency": plasma.plasma_frequency}


@app.get("/api/solar/parker")
def get_parker_spiral(r: float = Query(..., ge=0), v_sw: float = Query(400000, gt=0)):
    """
    Calculate Parker Spiral Angle.
    """
    ps = ParkerSpiral(v_sw=v_sw)
    return {"spiral_angle": ps.spiral_angle(r)}


@app.get("/api/solar/sunspot")
def get_sunspot_temperature(ratio: float = Query(..., ge=0)):
    """
    Estimate Sunspot Temperature.
    """
    T = sunspot_temperature(ratio)
    return {"temperature_k": T}


@app.get("/api/magnetosphere/standoff")
def get_magnetopause_standoff(
    density: float = Query(..., gt=0), velocity: float = Query(..., gt=0), Bz: float = 0
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
