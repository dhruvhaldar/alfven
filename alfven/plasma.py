import numpy as np
from .utils import e, m_e, eps_0, k_B

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
        return np.sqrt((eps_0 * k_B * self.T_k) / (self.n * e**2))

    @property
    def plasma_frequency(self):
        """
        Calculate the Electron Plasma Frequency (omega_pe).

        Returns:
            float: Plasma frequency in rad/s.
        """
        # omega_pe = sqrt(n * e^2 / (m_e * eps_0))
        return np.sqrt((self.n * e**2) / (m_e * eps_0))

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
        v_th = np.sqrt((k_B * self.T_k) / m_e)
        return (m_e * v_th) / (e * B)
