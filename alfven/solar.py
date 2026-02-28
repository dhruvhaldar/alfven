import math
from .utils import AU

class ParkerSpiral:
    def __init__(self, v_sw=400000, omega=2.7e-6):
        """
        Initialize Parker Spiral model.

        Args:
            v_sw (float): Solar wind velocity in m/s. Default 400 km/s.
            omega (float): Solar angular velocity in rad/s. Default 2.7e-6 rad/s.
        """
        self.v_sw = v_sw
        self.omega = omega

    def spiral_angle(self, r):
        """
        Calculate the Parker Spiral angle at a given distance r in the ecliptic plane.

        Args:
            r (float): Distance from the Sun in meters.

        Returns:
            float: Spiral angle in degrees (0 to 90).
        """
        # tan(psi) = (omega * r) / v_sw
        # We return the absolute angle relative to radial direction.
        psi_rad = math.atan((self.omega * r) / self.v_sw)
        return math.degrees(psi_rad)

def sunspot_temperature(intensity_ratio, T_photosphere=5778):
    """
    Estimate sunspot temperature based on intensity contrast.
    Using Stefan-Boltzmann law: I proportional to T^4.

    Args:
        intensity_ratio (float): I_spot / I_photosphere (0 to 1).
        T_photosphere (float): Photosphere temperature in K.

    Returns:
        float: Estimated sunspot temperature in K.
    """
    return T_photosphere * (intensity_ratio)**0.25
