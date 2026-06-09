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
        self._density = density
        self._velocity = velocity
        self._Bz = Bz
        self._B0 = _B0
        self._radius_re = None

    @property
    def density(self):
        return self._density

    @density.setter
    def density(self, value):
        self._density = value
        self._radius_re = None

    @property
    def velocity(self):
        return self._velocity

    @velocity.setter
    def velocity(self, value):
        self._velocity = value
        self._radius_re = None

    @property
    def Bz(self):
        return self._Bz

    @Bz.setter
    def Bz(self, value):
        self._Bz = value

    @property
    def B0(self):
        return self._B0

    @B0.setter
    def B0(self, value):
        self._B0 = value
        self._radius_re = None

    @property
    def radius_re(self):
        """
        Calculate the standoff distance in Earth Radii (Re).
        Using Chapman-Ferraro pressure balance (simplified):
        (R/Re)^6 = B0^2 / (mu_0 * rho * v^2)
        Assuming specular reflection (factor of 2 in dynamic pressure).
        """
        if self._radius_re is None:
            v = self._velocity
            P_dyn_scaled = self._density * (v * v)

            if P_dyn_scaled <= 0:
                return float('inf')

            # Use precomputed constant if B0 hasn't been dynamically overridden
            if self._B0 == _B0:
                R_ratio_6 = _B0_SQ_DIV_MU0_MP / P_dyn_scaled
            else:
                # Fallback if self._B0 was modified
                R_ratio_6 = (self._B0 * self._B0) / (mu_0 * m_p * P_dyn_scaled)

            self._radius_re = R_ratio_6**(1/6)
        return self._radius_re
