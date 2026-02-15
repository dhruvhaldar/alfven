from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from typing import List
import os
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


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    response = JSONResponse(
        status_code=500, content={"detail": "Internal Server Error"}
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


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
