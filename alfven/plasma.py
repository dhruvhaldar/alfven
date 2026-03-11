import math
from .utils import e, m_e, eps_0, k_B

# Optimization: Precompute physical constant combinations
_DEBYE_CONST = eps_0 * k_B / (e**2)
_PLASMA_FREQ_CONST = (e**2) / (m_e * eps_0)
_VTH_CONST = k_B / m_e
_LARMOR_CONST = m_e / e

class PlasmaState:
    """
    Represents the state of a plasma defined by density and temperature.
    """
    def __init__(self, n, T_ev):
        """
        Initialize PlasmaState.

        Args:
            n (float): Electron density in m^-3.
            T_ev (float): Electron temperature in eV.
        """
        self.n = n
        self.T_ev = T_ev
        # Convert Temperature to Kelvin: T(K) = T(eV) * e / k_B
        self.T_k = T_ev * e / k_B

    @property
    def debye_length(self):
        """
        Calculate the Debye Length (lambda_D).

        Returns:
            float: Debye length in meters.
        """
        # lambda_D = sqrt(eps0 * k_B * T / (n * e^2))
        # Optimization: Use precomputed constant term for speed
        return math.sqrt(_DEBYE_CONST * self.T_k / self.n)

    @property
    def plasma_frequency(self):
        """
        Calculate the Electron Plasma Frequency (omega_pe).

        Returns:
            float: Plasma frequency in rad/s.
        """
        # omega_pe = sqrt(n * e^2 / (m_e * eps_0))
        # Optimization: Use precomputed constant term for speed
        return math.sqrt(self.n * _PLASMA_FREQ_CONST)

    def larmor_radius(self, B):
        """
        Calculate the Larmor Radius (r_L) for an electron.
        Using thermal velocity v_th = sqrt(k_B * T / m_e).

        Args:
            B (float): Magnetic field strength in Tesla.

        Returns:
            float: Larmor radius in meters.
        """
        if B == 0:
            return float('inf')
        # Optimization: Use precomputed constant terms
        v_th = math.sqrt(_VTH_CONST * self.T_k)
        return (_LARMOR_CONST * v_th) / B
