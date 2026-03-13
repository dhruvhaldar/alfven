from .utils import m_p, mu_0, Re

# Optimization: Precompute physical constant combinations
# B0 is Earth's magnetic field at equator in Tesla (31,200 nT)
_B0 = 3.12e-5
_B0_SQ_DIV_MU0_MP = (_B0 * _B0) / (mu_0 * m_p)

class Magnetopause:
    def __init__(self, density, velocity, Bz=0):
        """
        Initialize Magnetopause model.

        Args:
            density (float): Solar wind density in m^-3.
            velocity (float): Solar wind velocity in m/s.
            Bz (float): IMF Bz component in Tesla. Default 0.
        """
        self.density = density
        self.velocity = velocity
        self.Bz = Bz
        self.B0 = _B0

    @property
    def radius_re(self):
        """
        Calculate the standoff distance in Earth Radii (Re).
        Using Chapman-Ferraro pressure balance (simplified):
        (R/Re)^6 = B0^2 / (mu_0 * rho * v^2)
        Assuming specular reflection (factor of 2 in dynamic pressure).
        """
        v = self.velocity
        P_dyn_scaled = self.density * (v * v)

        if P_dyn_scaled <= 0:
            return float('inf')

        # Use precomputed constant if B0 hasn't been dynamically overridden
        if self.B0 == _B0:
            R_ratio_6 = _B0_SQ_DIV_MU0_MP / P_dyn_scaled
        else:
            # Fallback if self.B0 was modified
            R_ratio_6 = (self.B0 * self.B0) / (mu_0 * m_p * P_dyn_scaled)

        return R_ratio_6**(1/6)
