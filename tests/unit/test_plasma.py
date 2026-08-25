import pytest
from alfven.plasma import PlasmaState, alfven_speed

def test_debye_length():
    """
    Verifies Debye Length calculation: lambda_D = sqrt(eps0 * k * Te / (n * e^2))
    """
    # Typical Solar Wind: n=5 cm^-3, T=10 eV
    sw = PlasmaState(n=5e6, T_ev=10)

    # Expected: ~10.5 meters
    assert abs(sw.debye_length - 10.5) < 1.0

def test_larmor_radius():
    sw = PlasmaState(n=5e6, T_ev=10)
    # B = 5 nT (Typical IMF)
    rL = sw.larmor_radius(B=5e-9)
    # rL = m v / e B
    # v = sqrt(k T / m) ~ sqrt(1.38e-23 * 116000 / 9.1e-31) ~ 1.3e6 m/s
    # rL ~ 9.1e-31 * 1.3e6 / (1.6e-19 * 5e-9) ~ 11.8e-25 / 8e-28 ~ 1.4e3 m = 1.4 km
    assert rL > 1000 and rL < 2000

def test_alfven_speed_for_typical_solar_wind():
    speed = alfven_speed(B=5e-9, ion_density=5e6)
    assert 48_000 < speed < 50_000

def test_plasma_parameter_is_collective():
    solar_wind = PlasmaState(n=5e6, T_ev=10)
    assert solar_wind.plasma_parameter > 1
    assert 1.3e6 < solar_wind.thermal_speed < 1.4e6
    assert 870 < solar_wind.electron_gyrofrequency(5e-9) < 890

def test_alfven_speed_rejects_non_positive_inputs():
    with pytest.raises(ValueError):
        alfven_speed(B=0, ion_density=5e6)
