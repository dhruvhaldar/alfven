import math
from .utils import e, m_e, eps_0, k_B

# Optimization: Precompute physical constant combinations and algebraically simplify formula terms
_DEBYE_CONST_SQRT = math.sqrt(eps_0 / e)
_PLASMA_FREQ_CONST = (e**2) / (m_e * eps_0)
_LARMOR_CONST_SQRT = math.sqrt(m_e / e)
_EV_TO_K = e / k_B

# Optimization: Precompute square root of _PLASMA_FREQ_CONST for direct use
_PLASMA_FREQ_CONST_SQRT = math.sqrt(_PLASMA_FREQ_CONST)

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

    @property
    def n(self):
        return self._n

    @n.setter
    def n(self, value):
        self._n = value
        # Optimization: Precompute square root of density
        self._sqrt_n = math.sqrt(value)

    @property
    def T_ev(self):
        return self._T_ev

    @T_ev.setter
    def T_ev(self, value):
        self._T_ev = value
        # Convert Temperature to Kelvin: T(K) = T(eV) * e / k_B
        # Optimization: use precomputed conversion constant to eliminate division overhead
        self.T_k = value * _EV_TO_K
        # Optimization: Precompute square root of temperature
        self._sqrt_T_ev = math.sqrt(value)

    @property
    def debye_length(self):
        """
        Calculate the Debye Length (lambda_D).

        Returns:
            float: Debye length in meters.
        """
        # lambda_D = sqrt(eps0 * k_B * T / (n * e^2))
        # Optimization: Use algebraically simplified, precomputed constant term and cached square roots for speed
        return _DEBYE_CONST_SQRT * (self._sqrt_T_ev / self._sqrt_n)

    @property
    def plasma_frequency(self):
        """
        Calculate the Electron Plasma Frequency (omega_pe).

        Returns:
            float: Plasma frequency in rad/s.
        """
        # omega_pe = sqrt(n * e^2 / (m_e * eps_0))
        # Optimization: Use precomputed constant term and cached square root for speed
        return self._sqrt_n * _PLASMA_FREQ_CONST_SQRT

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
        # Optimization: Use algebraically simplified, precomputed constant terms and cached square root
        return (_LARMOR_CONST_SQRT * self._sqrt_T_ev) / B
