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
        # Optimization: Precompute ratio for faster tangent argument calculation
        self._omega_div_v = omega / v_sw
        # Optimization: Precompute factor to eliminate math.degrees function call overhead
        self._deg_factor = 180.0 / math.pi

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
        # Optimization: use precomputed ratio and multiplication factor to avoid division and function calls
        return math.atan(self._omega_div_v * r) * self._deg_factor

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
