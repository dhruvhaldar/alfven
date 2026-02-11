from alfven.magnetosphere import Magnetopause

def test_geostationary_exposure():
    """
    E2E Test: Does a severe solar storm compress the magnetopause
    inside Geosynchronous Orbit (6.6 Re)?
    """
    # Simulate Carrington-class event
    storm = Magnetopause(density=50e6, velocity=1200e3, Bz=-20e-9)

    # If radius < 6.6 Re, satellites are in the magnetosheath
    assert storm.radius_re < 6.6
