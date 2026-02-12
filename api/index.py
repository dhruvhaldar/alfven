from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import os
from alfven import PlasmaState, ParkerSpiral, Magnetopause, ChapmanLayer, AuroraPower, sunspot_temperature

app = FastAPI(title="Alfven API", description="Space Weather & Plasma Physics Simulator API")

# Input Models

class PlasmaInput(BaseModel):
    n: float
    T_ev: float

class LarmorInput(BaseModel):
    T_ev: float
    B: float

class SolarInput(BaseModel):
    v_sw: float
    r: float

class MagnetosphereInput(BaseModel):
    density: float
    velocity: float
    Bz: float = 0

class LayerParams(BaseModel):
    h0: float
    H: float
    n_max: float

class IonosphereInput(BaseModel):
    layers: List[LayerParams]
    min_h: float
    max_h: float
    steps: int = 100

class AuroraInput(BaseModel):
    E_field: float
    sigma_P: float
    area: float

# Endpoints

@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/api/plasma/debye")
def get_debye_length(n: float, T_ev: float):
    """
    Calculate Debye Length.
    """
    plasma = PlasmaState(n, T_ev)
    return {"debye_length": plasma.debye_length}

@app.get("/api/plasma/larmor")
def get_larmor_radius(T_ev: float, B: float):
    """
    Calculate Larmor Radius.
    """
    # Use dummy density n=1e6 since it doesn't affect Larmor radius
    plasma = PlasmaState(1e6, T_ev)
    return {"larmor_radius": plasma.larmor_radius(B)}

@app.get("/api/plasma/frequency")
def get_plasma_frequency(n: float):
    """
    Calculate Plasma Frequency.
    """
    plasma = PlasmaState(n, 1.0) # T doesn't matter
    return {"plasma_frequency": plasma.plasma_frequency}

@app.get("/api/solar/parker")
def get_parker_spiral(r: float, v_sw: float = 400000):
    """
    Calculate Parker Spiral Angle.
    """
    ps = ParkerSpiral(v_sw=v_sw)
    return {"spiral_angle": ps.spiral_angle(r)}

@app.get("/api/solar/sunspot")
def get_sunspot_temperature(ratio: float):
    """
    Estimate Sunspot Temperature.
    """
    T = sunspot_temperature(ratio)
    return {"temperature_k": T}

@app.get("/api/magnetosphere/standoff")
def get_magnetopause_standoff(density: float, velocity: float, Bz: float = 0):
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
    profile = None
    for layer_params in data.layers:
        layer = ChapmanLayer(layer_params.h0, layer_params.H, layer_params.n_max)
        if profile is None:
            profile = layer
        else:
            profile += layer # __add__ returns ChapmanProfile

    if profile:
        result = profile.get_profile_data(data.min_h, data.max_h, data.steps)
        return result
    return {"altitude": [], "density": []}

@app.post("/api/aurora/power")
def get_aurora_power(data: AuroraInput):
    """
    Estimate Auroral Power.
    """
    ap = AuroraPower(data.E_field, data.sigma_P, data.area)
    return {
        "dissipated_power": ap.dissipated_power,
        "sheet_current": ap.sheet_current
    }

# Mount static files for local development
if os.path.exists("public"):
    app.mount("/", StaticFiles(directory="public", html=True), name="static")
